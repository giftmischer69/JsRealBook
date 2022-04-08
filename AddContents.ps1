Get-ChildItem ".\build\pdf\" `
    | ForEach-Object {$i=0} { "$i : $($_.Name.Replace(".pdf", " ").Replace("_", " ")) \par"; $i++} `
    | Add-Content ".\build\cover.rtf"
Write-Output "\f1\fs22\par}" | Add-Content ".\build\cover.rtf"
