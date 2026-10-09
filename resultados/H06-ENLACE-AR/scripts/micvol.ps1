param([string]$set = "")
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
 int f(); int g(); int h();
 int SetMasterVolumeLevel(float l, Guid c); int SetMasterVolumeLevelScalar(float l, Guid c);
 int GetMasterVolumeLevel(out float l); int GetMasterVolumeLevelScalar(out float l);
 int a(); int b(); int c(); int d(); int SetMute(bool m, Guid c); int GetMute(out bool m);
 int j(); int k(); int l(); int m(); int GetVolumeRange(out float mn, out float mx, out float st);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref Guid id, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int f(); int GetDefaultAudioEndpoint(int flow, int role, out IMMDevice d); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumerator {}
public class Mic {
 static IAudioEndpointVolume V() {
  var en = (IMMDeviceEnumerator)(new MMDeviceEnumerator()); IMMDevice d; en.GetDefaultAudioEndpoint(1, 0, out d);
  var iid = typeof(IAudioEndpointVolume).GUID; object o; d.Activate(ref iid, 23, IntPtr.Zero, out o); return (IAudioEndpointVolume)o; }
 public static string Get() { var v=V(); float s,db,mn,mx,st; bool m; v.GetMasterVolumeLevelScalar(out s); v.GetMasterVolumeLevel(out db); v.GetVolumeRange(out mn,out mx,out st); v.GetMute(out m);
  return String.Format("escalar {0:F2}, {1:F1} dB (faixa {2:F1} a {3:F1}), mudo {4}", s, db, mn, mx, m); }
 public static void SetDb(float db) { V().SetMasterVolumeLevel(db, Guid.Empty); }
}
"@
if ($set -ne "") { [Mic]::SetDb([float]$set) }
[Mic]::Get()
