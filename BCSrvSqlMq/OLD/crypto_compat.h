// crypto_compat.h
// Fase 6: Resolver conflitos entre cryptlib.h e wincrypt.h
//
// PROBLEMA: wincrypt.h (Windows) e cryptlib.h definem macros com mesmo nome
// SOLUÇÃO: Incluir este header DEPOIS dos headers MFC mas ANTES de cryptlib.h

#ifndef CRYPTO_COMPAT_H
#define CRYPTO_COMPAT_H

// Desfazer todas as macros do wincrypt.h que conflitam com cryptlib.h
// Estas são redefinidas como enums pelo cryptlib.h

#ifdef CRYPT_MODE_ECB
#undef CRYPT_MODE_ECB
#endif

#ifdef CRYPT_MODE_CBC
#undef CRYPT_MODE_CBC
#endif

#ifdef CRYPT_MODE_CFB
#undef CRYPT_MODE_CFB
#endif

#ifdef CRYPT_MODE_OFB
#undef CRYPT_MODE_OFB
#endif

#ifdef CRYPT_MODE_CTS
#undef CRYPT_MODE_CTS
#endif

// Outros conflitos potenciais
#ifdef CRYPT_EXPORTABLE
#undef CRYPT_EXPORTABLE
#endif

#ifdef CRYPT_USER_PROTECTED
#undef CRYPT_USER_PROTECTED
#endif

#endif // CRYPTO_COMPAT_H
