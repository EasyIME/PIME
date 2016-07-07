// MD5 plugin. 
// Be sure to add the RSA license notice somewhere in your installer.
// 
// Matthew "IGx89" Lieder
//  Author
//
// KJD
//  -modified to reduce size and use exdll.h
//   (reduced to about 6KB uncompressed, by removing CRTL dependency)
//
// Davy Durham
//  -MD5.cpp fix (correct for loop used to replace memset, exceeded bounds)
//
// Shengalts Aleksander aka Instructor
//  -New command: "GetMD5Random"
//  -Changed names: "GetFileMD5" -> "GetMD5File", "GetMD5" -> "GetMD5String"
//  -Fixed: string lenght error
//
// KJD
//  -added dual exports for compatibility with prior versions
//
// KJD
//  -updated Exdll.h to pluginapi.h, enable building for NSIS & Unicode NSIS


#ifdef NSIS_UNICODE  /* MD5.cpp should be compiled in ANSI mode */
#define UNICODE
#define _UNICODE
#endif


#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "MD5.h"

unsigned char staticCnvBuffer[1024*2];
#ifdef UNICODE
#define wcslen lstrlenW
#define wcscpy lstrcpyW
#define wcsncpy lstrcpynW
#define wcscat lstrcatW
#define wcscmp lstrcmpW
#define wcscmpi lstrcmpiW
char * _T2A(unsigned short *wideStr)
{
	WideCharToMultiByte(CP_ACP, 0, wideStr, -1, (char *)staticCnvBuffer, sizeof(staticCnvBuffer), NULL, NULL);
	return (char *)staticCnvBuffer;
}
#define _A2T(x) _A2U(x)
#else
#define strlen lstrlenA
#define strcpy lstrcpyA
#define strncpy lstrcpynA
#define strcat lstrcatA
#define strcmp lstrcmpA
#define strcmpi lstrcmpiA
#define _T2A(x) (x)
#define _A2T(x) (x)
#endif
unsigned short * _A2U(char *ansiStr)
{
	MultiByteToWideChar(CP_ACP, 0, ansiStr, -1, (unsigned short *)staticCnvBuffer, sizeof(staticCnvBuffer)/2);
	return (unsigned short *)staticCnvBuffer;
}

#include "pluginapi.h"


void *operator new( unsigned int num_bytes )
{
  return GlobalAlloc(GPTR,num_bytes);
}
void operator delete( void *p ) { if (p) GlobalFree(p); }


/* buffer for retrieving arguments from NSIS's stack into, outside func to avoid calls to __stkchk */
TCHAR strarg[1024*sizeof(TCHAR)];

#ifdef ENABLE_GETMD5FILE
extern "C" void __declspec( dllexport ) GetMD5File(HWND hwndParent, int string_size, 
								   TCHAR *variables, stack_t **stacktop)
{
	EXDLL_INIT();

	// generate MD5sum of file
	{
		char *buf=NULL;

		popstring(strarg);
		buf = MD5File(_T2A(strarg));
		pushstring(_A2T(buf));
		delete buf;
	}
}
#endif // ENABLE_GETMD5FILE

#ifdef ENABLE_GETMD5STRING
extern "C" void __declspec( dllexport ) GetMD5String(HWND hwndParent, int string_size, 
								TCHAR *variables, stack_t **stacktop)
{
	EXDLL_INIT();

	// generate MD5sum of string
	{
		char *buf=NULL;

		popstring(strarg);
		buf = MD5String(_T2A(strarg));
		pushstring(_A2T(buf));
		delete buf;
	}
}
#endif // ENABLE_GETMD5STRING

#ifdef ENABLE_GETMD5RANDOM
extern "C" void __declspec( dllexport ) GetMD5Random(HWND hwndParent, int string_size, 
								TCHAR *variables, stack_t **stacktop)
{
	EXDLL_INIT();

	// generate random MD5sum
	{
		DWORD dwTickCount=0;
		char lTickCount[1024];
		char *buf=NULL;

		Sleep(1);
		dwTickCount=GetTickCount();
		wsprintfA(lTickCount,"%d",dwTickCount);
		buf = MD5String(lTickCount);
		pushstring(_A2T(buf));
		delete buf;
	}
}
#endif // ENABLE_GETMD5RANDOM

extern "C" BOOL WINAPI _DllMainCRTStartup(HANDLE hInst, ULONG ul_reason_for_call, LPVOID lpReserved)
{
	return TRUE;
}
