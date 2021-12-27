#include <Windows.h>

#if defined(_MSC_VER) && _MSC_VER+0 >= 1400
#if defined(_MSC_FULL_VER) && _MSC_FULL_VER+0 >= 140050727
#include <intrin.h>
#else
EXTERN_C void __stosb(BYTE*,BYTE,size_t);
#endif
#pragma intrinsic(__stosb)
#define CRTINTRINSIC_memset(p,c,s) __stosb((BYTE*)(p),(BYTE)(c),(s))
#endif

extern "C" void* __cdecl memset(void *p, int c, size_t z)
{
#ifdef CRTINTRINSIC_memset
  CRTINTRINSIC_memset(p, c, z);
#else
  BYTE *pb = reinterpret_cast<BYTE*>(p);
  for(size_t i=0; i<z; ++i, ++pb)
    (*pb) = c;
#endif
  return p;
}

extern "C" const char* __cdecl strstr(const char *str, const char *target)
{
  if (!*target) return (char*)str;
  char *p1 = (char*)str, *p2 = (char*)target;
  char *p1Adv = (char*)str;
  while (*++p2)
    p1Adv++;
  while (*p1Adv)
  {
    char *p1Begin = p1;
    p2 = (char*)target;
    while (*p1 && *p2 && *p1 == *p2)
    {
      p1++;
      p2++;
    }
    if (!*p2)
      return p1Begin;
    p1 = p1Begin + 1;
    p1Adv++;
  }
  return NULL;
}

extern "C" const wchar_t* __cdecl wcsstr(const wchar_t *str, const wchar_t *target)
{
  if (!*target) return (wchar_t*)str;
  wchar_t *p1 = (wchar_t*)str, *p2 = (wchar_t*)target;
  wchar_t *p1Adv = (wchar_t*)str;
  while (*++p2)
    p1Adv++;
  while (*p1Adv)
  {
    wchar_t *p1Begin = p1;
    p2 = (wchar_t*)target;
    while (*p1 && *p2 && *p1 == *p2)
    {
      p1++;
      p2++;
    }
    if (!*p2)
      return p1Begin;
    p1 = p1Begin + 1;
    p1Adv++;
  }
  return NULL;
}

extern "C" const char* __cdecl strchr(const char* s, int ch)
{
  while(*s && *s != ch)
    ++s;
  return s;
}

extern "C" const wchar_t* __cdecl wcschr(const wchar_t* s, wchar_t ch)
{
  while(*s && *s != ch)
    ++s;
  return s;
}

extern "C" const char* __cdecl strrchr(const char* s, int c)
{
  char *rtnval = 0;
  do {
    if (*s == c)
      rtnval = (char*) s;
  } while (*s++);
  return rtnval;
}

extern "C" const wchar_t* __cdecl wcsrchr(const wchar_t* s, wchar_t c)
{
  wchar_t *rtnval = 0;
  do {
    if (*s == c)
      rtnval = (wchar_t*) s;
  } while (*s++);
  return rtnval;
}