"""Plugin authoring guide."""

A plugin is a directory under the plugins root with a `plugin.json` manifest.

```json
{
  "name": "provider.example",
  "version": "0.1.0",
  "interface": ["emit","scan","notify","detect"]
}
```

Supported interfaces:
- `emit`: write IaC/artifacts for a provider
- `scan`: mutate DeploymentPackage with findings
- `notify`: external issue/comment creation
- `detect`: repo inspection returning AppSpec

Discovery:
- CLI scans `<plugins_dir>/*/plugin.json`
- The manager loads any manifest it finds; optional deps stay in the plugin package

Packaging:
- Put plugins in `plugins/<category>/<name>/`
- Keep plugin code out of `ai_deploy/core/`
