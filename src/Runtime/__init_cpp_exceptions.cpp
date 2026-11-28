#include "NMWException.h"
#include "__ppc_eabi_linker.h"

#ifdef __cplusplus
extern "C" {
#endif

extern void __init_cpp_exceptions(void);
extern void __fini_cpp_exceptions(void);
extern void __destroy_global_chain(void);

#ifdef __cplusplus
}
#endif

static int fragmentID = -2;

void __init_cpp_exceptions(void) {
    if (fragmentID == -2) {
        register char* temp;
        asm {
            mr temp,r2
        }

        fragmentID = __register_fragment(_eti_init_info, (char*)temp);
    }
}

void __fini_cpp_exceptions(void) {
    if (fragmentID != -2) {
        __unregister_fragment(fragmentID);
        fragmentID = -2;
    }
}

#pragma force_active on

#pragma section ".ctors$10"
__declspec(section ".ctors$10") extern void* const __init_cpp_exceptions_reference = __init_cpp_exceptions;
#pragma section ".dtors$10"
__declspec(section ".dtors$10") extern void* const __destroy_global_chain_reference = __destroy_global_chain;
#pragma section ".dtors$15"
__declspec(section ".dtors$15") extern void* const __fini_cpp_exceptions_reference = __fini_cpp_exceptions;