$Driver = Start-SeNewEdge -StartURL "http://127.0.0.1:5000/login" -WebDriverDirectory "C:\Users\plamena.licheva\Downloads\edgedriver_win64"
$Button = Get-SeElement -Driver $Driver -By TagName -Selection "button"
Invoke-SeClick -Element $Button
$Username = Get-SeElement -Driver $Driver -By Name -Selection "username"
Send-SeKeys -Element $Username -Keys "plami"
$Password = Get-SeElement -Driver $Driver -By Name -Selection "password"
Send-SeKeys -Element $Password -Keys "plami"
$Button = Get-SeElement -Driver $Driver -By TagName -Selection "button"
Invoke-SeClick -Element $Button