[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$GameDirectory='P:\AI\gclx-codexrun\game',[switch]$Restore)
$ErrorActionPreference='Stop'
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$game=(Resolve-Path -LiteralPath $GameDirectory).Path
if(-not $game.StartsWith('P:\',[StringComparison]::OrdinalIgnoreCase)){throw 'Game directory must be on P:.'}
$exe=Join-Path $game 'GUILTY CROWN LOST XMAS.exe'
$active=@(Get-CimInstance Win32_Process -Filter "Name='GUILTY CROWN LOST XMAS.exe'" | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.Equals($exe,[StringComparison]::OrdinalIgnoreCase) })
if($active.Count){throw '게임이 실행 중입니다. 저장하고 종료한 뒤 다시 실행하세요.'}
$target=Join-Path $game 'nss.npa'
$runtime=Join-Path $game 'n2hd_runtime.dll'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -ne $manifest.runtime_sha256){throw '기준 최신판 DLL과 다릅니다. 설치를 중단합니다.'}
$current=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
$payload=Join-Path $PSScriptRoot 'nss.npa'
if($Restore){
 $expected=$manifest.patch_sha256;$wanted=$manifest.baseline_nss_sha256
 $payload=Join-Path $PSScriptRoot ('backups\'+$wanted+'\nss.npa')
}else{$expected=$manifest.baseline_nss_sha256;$wanted=$manifest.patch_sha256}
if($current -eq $wanted){Write-Host '이미 요청한 버전이 적용되어 있습니다.';return}
if($current -ne $expected){throw '기준 최신판 NSS와 다릅니다. 기존 변경을 보호하기 위해 설치를 중단합니다.'}
if((Get-FileHash -LiteralPath $payload -Algorithm SHA256).Hash -ne $wanted){throw '패치 또는 백업 파일 해시가 일치하지 않습니다.'}
if(-not $PSCmdlet.ShouldProcess($target,'가사 패치 파일 교체 및 원본 백업')){return}
$backupDir=Join-Path $PSScriptRoot ('backups\'+$current)
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$backup=Join-Path $backupDir 'nss.npa'
if(Test-Path -LiteralPath $backup){if((Get-FileHash -LiteralPath $backup).Hash -ne $current){throw '기존 백업이 다른 파일입니다.'}}else{Copy-Item -LiteralPath $target -Destination $backup}
if((Get-FileHash -LiteralPath $backup).Hash -ne $current){throw '백업 검증에 실패했습니다.'}
$staged=Join-Path $game ('nss.npa.codex-'+[Guid]::NewGuid().ToString('N'))
try{
 Copy-Item -LiteralPath $payload -Destination $staged
 if((Get-FileHash -LiteralPath $staged).Hash -ne $wanted){throw '복사 검증에 실패했습니다.'}
 [IO.File]::Replace($staged,$target,$backup)
}finally{if(Test-Path -LiteralPath $staged){Remove-Item -LiteralPath $staged}}
if((Get-FileHash -LiteralPath $target).Hash -ne $wanted){throw '최종 검증에 실패했습니다.'}
$receipt=[ordered]@{action=$(if($Restore){'restore'}else{'install'});target=$target;before_sha256=$current;after_sha256=$wanted;backup=$backup;verified=$true}
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'installation-receipt.json') -Encoding UTF8
Write-Host '완료했습니다. Korean4K.exe로 다시 실행하세요.'
