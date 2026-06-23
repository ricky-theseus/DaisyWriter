param(
  [Parameter(Mandatory = $true)]
  [string]$RepoUrl
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

# Add remote
git -C $root remote add origin $RepoUrl

# First commit
git -C $root add -A
git -C $root commit -m "feat: initial release v1.0.0"

# Push
git -C $root push -u origin master

Write-Output "Done! Pushed to $RepoUrl"
