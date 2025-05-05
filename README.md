# python-github-action-template
A Github Action to generate Issues when base localization file is updated.
This action assumes that localization files are simple JSON files with a dictionary containing key-value pairs.

Example localization data structure: [Link](https://github.com/Mythical-Github/ue4ss_installer_gui/tree/dev/assets/base/assets/localization)

Default input parameters:
```yaml
base-dir:
  description: 'Directory containing localization files'
  required: false
  default: 'assets/base/assets/localization'
base-file:
  description: 'Native translation file'
  required: false
  default: 'en.json'
branch:
  description: 'Branch to operate on'
  required: false
  default: 'main'
commit:
  description: 'Old commit to check against. Defaults to last'
  required: false
  default: 'HEAD^'
maintainers:
  description: 'Path to maintainers JSON file'
  required: false
  default: 'localization_maintainers.json'
template:
  description: 'Path to YAML markdown template'
  required: false
  default: '/scripts/template.yml'
```

Example Workflow:

```yaml
name: Create localization help issue

on:
  workflow_dispatch:
    inputs:
      commit:
        description: 'Commit to compare to (last by default)'
        type: string
        default: 'HEAD^'
        required: true
      template:
        description: 'Custom YAML template for Markdown (if needed)'
        type: string
        default: '/scripts/template.yml'
        required: true

jobs:
  call-external-python-action:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout your own repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.ref }}

      - name: Run Python Action from external repo
        id: run_action
        uses: Knutschbert/create-localization-issue@main  # Or better: use a commit SHA or tag
        with:
          # base_dir: ""
          # base_file: ""
          branch: ${{ github.ref }}
          commit: ${{ github.event.inputs.commit }}
          # maintainers: ""
          template: ${{ github.event.inputs.template }}
      # - name: Print markdown outputs
      #   run: echo "One ${{ steps.run_action.outputs.issue-title }} Two ${{ steps.run_action.outputs.issue-body }}"
      - name: Create issue
        uses: dacbd/create-issue-action@main
        with:
          token: ${{ github.token }}
          title: ${{ steps.run_action.outputs.issue-title }}
          body: ${{ steps.run_action.outputs.issue-body }}
          labels:
            - localization
            - automated
            - help wanted
```