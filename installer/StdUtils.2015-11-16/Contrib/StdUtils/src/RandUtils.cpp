///////////////////////////////////////////////////////////////////////////////
// StdUtils plug-in for NSIS
// Copyright (C) 2004-2015 LoRd_MuldeR <MuldeR2@GMX.de>
//
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 2.1 of the License, or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public
// License along with this library; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
//
// http://www.gnu.org/licenses/lgpl-2.1.txt
///////////////////////////////////////////////////////////////////////////////

#include "RandUtils.h"

#include "Mutex.h"
#include "UnicodeSupport.h"
#include "msvc_utils.h"

//Global
extern RTL_CRITICAL_SECTION g_pStdUtilsMutex;

//Prototype
typedef BOOLEAN (__stdcall *TRtlGenRandom)(PVOID RandomBuffer, ULONG RandomBufferLength);

static bool s_secure_rand_init = false;
static TRtlGenRandom s_pRtlGenRandom = NULL;

static inline unsigned int my_rand(void)
{
	return (static_cast<unsigned int>(rand()) << 16) ^ static_cast<unsigned int>(rand());
}

/* Robert Jenkins' 96 bit Mix Function */
static unsigned int mix_function(const unsigned int x, const unsigned int y, const unsigned int z)
{
	unsigned int a = x;
	unsigned int b = y;
	unsigned int c = z;
	
	a=a-b;  a=a-c;  a=a^(c >> 13);
	b=b-c;  b=b-a;  b=b^(a << 8); 
	c=c-a;  c=c-b;  c=c^(b >> 13);
	a=a-b;  a=a-c;  a=a^(c >> 12);
	b=b-c;  b=b-a;  b=b^(a << 16);
	c=c-a;  c=c-b;  c=c^(b >> 5);
	a=a-b;  a=a-c;  a=a^(c >> 3);
	b=b-c;  b=b-a;  b=b^(a << 10);
	c=c-a;  c=c-b;  c=c^(b >> 15);

	return c;
}

static inline void init_rand(void)
{
	MutexLocker locker(&g_pStdUtilsMutex);

	if(!s_secure_rand_init)
	{
		srand(static_cast<unsigned int>(time(NULL)));

		HMODULE advapi32 = GetModuleHandle(T("Advapi32.dll"));
		if(advapi32)
		{
			s_pRtlGenRandom = reinterpret_cast<TRtlGenRandom>(GetProcAddress(advapi32, "SystemFunction036"));
		}

		s_secure_rand_init = true;
	}
}

unsigned int next_rand(void)
{
	init_rand();

	if(s_pRtlGenRandom)
	{
		unsigned int rnd;
		if(s_pRtlGenRandom(&rnd, sizeof(unsigned int)))
		{
			return rnd;
		}
	}

	const unsigned int x = my_rand();
	const unsigned int y = my_rand();
	const unsigned int z = my_rand();
	
	return mix_function(x, y, z);
}
