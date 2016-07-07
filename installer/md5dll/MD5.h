/////////////////////////////////////////////////////////////////////////
// MD5.cpp
// Implementation file for MD5 class
//
// This C++ Class implementation of the original RSA Data Security, Inc.
// MD5 Message-Digest Algorithm is copyright (c) 2002, Gary McNickle.
// All rights reserved.  This software is a derivative of the "RSA Data
//  Security, Inc. MD5 Message-Digest Algorithm"
//
// You may use this software free of any charge, but without any
// warranty or implied warranty, provided that you follow the terms
// of the original RSA copyright, listed below.
//
// Original RSA Data Security, Inc. Copyright notice
/////////////////////////////////////////////////////////////////////////
//
// Copyright (C) 1991-2, RSA Data Security, Inc. Created 1991. All
// rights reserved.
//
// License to copy and use this software is granted provided that it
// is identified as the "RSA Data Security, Inc. MD5 Message-Digest
// Algorithm" in all material mentioning or referencing this software
// or this function.
// License is also granted to make and use derivative works provided
// that such works are identified as "derived from the RSA Data
// Security, Inc. MD5 Message-Digest Algorithm" in all material
// mentioning or referencing the derived work.
// RSA Data Security, Inc. makes no representations concerning either
// the merchantability of this software or the suitability of this
// software for any particular purpose. It is provided "as is"
// without express or implied warranty of any kind.
// These notices must be retained in any copies of any part of this
// documentation and/or software.
/////////////////////////////////////////////////////////////////////////

typedef unsigned       int uint4;
typedef unsigned short int uint2;
typedef unsigned      char uchar;

char* PrintMD5(uchar md5Digest[16]);
#if defined(ENABLE_GETMD5STRING) || defined (ENABLE_GETMD5RANDOM)
char* MD5String(char* szString);
#endif
#if defined(ENABLE_GETMD5FILE)
char* MD5File(char* szFilename);
#endif

class md5
{
// Methods
public:
	md5() { Init(); }
	void	Init();
	void	Update(uchar* chInput, uint4 nInputLen);
	void	Finalize();
	uchar*	Digest() { return m_Digest; }

private:

	void	Transform(uchar* block);
	void	Encode(uchar* dest, uint4* src, uint4 nLength);
	void	Decode(uint4* dest, uchar* src, uint4 nLength);


	inline	uint4	rotate_left(uint4 x, uint4 n)
	                 { return ((x << n) | (x >> (32-n))); }

	inline	uint4	F(uint4 x, uint4 y, uint4 z)
	                 { return ((x & y) | (~x & z)); }

	inline  uint4	G(uint4 x, uint4 y, uint4 z)
	                 { return ((x & z) | (y & ~z)); }

	inline  uint4	H(uint4 x, uint4 y, uint4 z)
	                 { return (x ^ y ^ z); }

	inline  uint4	I(uint4 x, uint4 y, uint4 z)
	                 { return (y ^ (x | ~z)); }

	inline	void	FF(uint4& a, uint4 b, uint4 c, uint4 d, uint4 x, uint4 s, uint4 ac)
	                 { a += F(b, c, d) + x + ac; a = rotate_left(a, s); a += b; }

	inline	void	GG(uint4& a, uint4 b, uint4 c, uint4 d, uint4 x, uint4 s, uint4 ac)
                     { a += G(b, c, d) + x + ac; a = rotate_left(a, s); a += b; }

	inline	void	HH(uint4& a, uint4 b, uint4 c, uint4 d, uint4 x, uint4 s, uint4 ac)
                     { a += H(b, c, d) + x + ac; a = rotate_left(a, s); a += b; }

	inline	void	II(uint4& a, uint4 b, uint4 c, uint4 d, uint4 x, uint4 s, uint4 ac)
                     { a += I(b, c, d) + x + ac; a = rotate_left(a, s); a += b; }

// Data
private:
	uint4		m_State[4];
	uint4		m_Count[2];
	uchar		m_Buffer[64];
	uchar		m_Digest[16];
	uchar		m_Finalized;

};