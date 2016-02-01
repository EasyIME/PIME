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

#pragma once

#include "StdUtils.h"

#define STD_HASHTYPE_CRC_32   0x1
#define STD_HASHTYPE_MD5_128  0x2
#define STD_HASHTYPE_SHA1_160 0x3
#define STD_HASHTYPE_SHA2_224 0x4
#define STD_HASHTYPE_SHA2_256 0x5
#define STD_HASHTYPE_SHA2_384 0x6
#define STD_HASHTYPE_SHA2_512 0x7
#define STD_HASHTYPE_SHA3_224 0x8
#define STD_HASHTYPE_SHA3_256 0x9
#define STD_HASHTYPE_SHA3_384 0xA
#define STD_HASHTYPE_SHA3_512 0xB
#define STD_HASHTYPE_BLK2_224 0xC
#define STD_HASHTYPE_BLK2_256 0xD
#define STD_HASHTYPE_BLK2_384 0xE
#define STD_HASHTYPE_BLK2_512 0xF


#ifndef STDUTILS_DISABLE_HASHES

bool ComputeHash_FromFile(const int hashType, const TCHAR *const fileName, TCHAR *const hashOut, const size_t hashOutSize);
bool ComputeHash_FromText(const int hashType, const TCHAR *const textData, TCHAR *const hashOut, const size_t hashOutSize);

#else //STDUTILS_DISABLE_HASHES

#define ComputeHash_FromFile(W,X,Y,Z) (false)
#define ComputeHash_FromText(W,X,Y,Z) (false)

#endif //STDUTILS_DISABLE_HASHES
