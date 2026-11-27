# Usage: win.ps1 shot OUT.png | click X Y | key KEYS   (X,Y relative to game client area, 1920x1080 scale)
param([string]$Cmd, [string]$A, [string]$B2)
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public struct RECT { public int L,T,R,B; }
public struct PT { public int X,Y; }
public class U {
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref PT p);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(int f,int x,int y,int d,int e);
}
"@
[U]::SetProcessDPIAware() | Out-Null
$p = Get-Process BewitchingSinners -ErrorAction Stop | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
$h = $p.MainWindowHandle
[U]::ShowWindow($h, 9) | Out-Null
$ws = New-Object -ComObject WScript.Shell
$ws.AppActivate($p.Id) | Out-Null
[U]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 250
$r = New-Object RECT; [U]::GetClientRect($h, [ref]$r) | Out-Null
$o = New-Object PT; [U]::ClientToScreen($h, [ref]$o) | Out-Null
$w = $r.R; $hh = $r.B
if ($Cmd -eq 'shot') {
  $bmp = New-Object System.Drawing.Bitmap $w, $hh
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($o.X, $o.Y, 0, 0, (New-Object System.Drawing.Size $w, $hh))
  $bmp.Save($A, [System.Drawing.Imaging.ImageFormat]::Png)
  "saved $w x $hh"
} elseif ($Cmd -eq 'click') {
  $x = [int]($o.X + [double]$A * $w / 1920); $y = [int]($o.Y + [double]$B2 * $hh / 1080)
  [U]::SetCursorPos($x-3, $y-3); Start-Sleep -Milliseconds 200; [U]::SetCursorPos($x, $y); Start-Sleep -Milliseconds 300
  [U]::mouse_event(2,0,0,0,0); Start-Sleep -Milliseconds 120; [U]::mouse_event(4,0,0,0,0)
  "clicked $x,$y"
} elseif ($Cmd -eq 'key') {
  $ws.SendKeys($A); "sent $A"
}
