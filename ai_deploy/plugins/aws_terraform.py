"""AWS Terraform emitter."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ai_deploy.core.types import DeploymentPackage

log = logging.getLogger(__name__)


def _resource_type(component_type: str) -> str:
    return {
        "vpc": "aws_vpc",
        "eks": "aws_eks_cluster",
        "ecs": "aws_ecs_cluster",
        "rds": "aws_db_instance",
        "s3": "aws_s3_bucket",
        "iam": "aws_iam_role",
        "cloudfront": "aws_cloudfront_distribution",
        "acm": "aws_acm_certificate",
    }.get(component_type, "aws_vpc")


def emit(package: DeploymentPackage, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)

    if package.security_findings:
        blocked = [f.finding for f in package.security_findings if f.severity == "high"]
        if blocked:
            raise RuntimeError(f"Blocked by security findings: {blocked}")

    non_actions = [c for c in package.components if c.type != "github_actions"]

    header = """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  default = "us-east-1"
}

variable "app_name" {
  default = "app"
}
""".lstrip()

    blocks = [header]

    if non_actions:
        for component in non_actions:
            if component.type == "eks":
                blocks.append(
                    """\
resource "aws_eks_cluster" "app" {
  name     = var.app_name
  role_arn = aws_iam_role.eks_role.arn

  vpc_config {
    subnet_ids = []
  }

  tags = { Name = var.app_name }
}

resource "aws_iam_role" "eks_role" {
  name = "${var.app_name}-eks-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "eks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_eks_node_group" "app" {
  cluster_name    = aws_eks_cluster.app.name
  node_group_name = "${var.app_name}-ng"
  node_role_arn   = aws_iam_role.eks_role.arn
  subnet_ids      = []

  instance_types = ["t3.medium"]
  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 4
  }

  tags = { Name = var.app_name }
}
""".lstrip()
                )
            else:
                blocks.append(
                    f"# component: {component.type}\nresource \"{_resource_type(component.type)}\" \"app\" {{\n  tags = {{ Name = var.app_name }}\n}}\n"
                )
    else:
        blocks.append(
            """
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_eks_cluster" "main" {
  name     = var.app_name
  role_arn = "" # TODO: IAM role
  vpc_config {
    subnet_ids = [] # TODO: subnet ids
  }
}
""".lstrip()
        )

    if any(c.type == "vpc" for c in package.components):
        blocks.append(
            """
resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "Managed by ai-deploy"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
""".lstrip()
        )

    if any(c.type == "github_actions" for c in package.components):
        wf = dest / "deploy.yml"
        wf.write_text(
            "name: ai-deploy\n"
            "on:\n"
            "  push:\n"
            "    branches: [main]\n"
            "jobs:\n"
            "  deploy:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            '      - uses: actions/checkout@v4\n'
            '      - uses: hashicorp/setup-terraform@v3\n'
            "      - run: terraform init\n"
            "      - run: terraform apply -auto-approve\n",
            encoding="utf-8",
        )

    (dest / "main.tf").write_text("\n".join(blocks), encoding="utf-8")
    (dest / "versions.tf").write_text(header, encoding="utf-8")
    log.info("emitted terraform package to %s", dest)
