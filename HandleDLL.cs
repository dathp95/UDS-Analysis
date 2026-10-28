using System.Runtime.InteropServices;

namespace CuiBapTool.ViewModel.Handle;

internal static class HandleDLL
{
	[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
	private delegate VKeyGenResult GenerateKeyExOpt(byte[] ipSeedArray, uint iSeedArraySize, uint iSecurityLevel, ref string ipVariant, ref string ipOptions, byte[] iopKeyArray, uint iMaxKeyArraySize, ref uint oActualKeyArraySize);

	private delegate VKeyGenResult GenerateKeyEx(byte[] ipSeedArray, uint iSeedArraySize, uint iSecurityLevel, ref string ipVariant, byte[] iopKeyArray, uint iMaxKeyArraySize, ref uint oActualKeyArraySize);

	private delegate bool ASAP1A_CCP_ComputeKeyFromSeed(byte[] ipSeedArray, uint iSeedArraySize, byte[] iopKeyArray, uint iMaxKeyArraySize, ref uint oActualKeyArraySize);

	public static bool CalulateKey(byte[] seedArr, uint level, ref byte[] _keyArr)
	{
		//Invalid MethodBodyBlock: Invalid method header: 0xCC
	}
}
