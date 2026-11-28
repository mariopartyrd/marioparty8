#ifndef GAME_MEMORY_H
#define GAME_MEMORY_H

#include <revolution/types.h>

#define HU_MEMNUM_OVL 0x10000000


typedef enum HeapID_e {
	HEAP_HEAP, //0
	HEAP_HEAP2, //1
	HEAP_AUDIO, //2
	HEAP_MODEL, //3
	HEAP_RECOVERY, //4
	HEAP_DVD, //5
	HEAP_SPACE, //6
	HEAP_MAX //7
} HEAPID;


#ifdef __cplusplus
extern "C" {
#endif

void HuMemInitAll(void);

void *HuMemInit(void *heap, u32 size);
void HuMemDCFlushAll(void);
void HuMemDCFlush(HEAPID heapId);
void *HuMemDirectMalloc(HEAPID heap, s32 size);
void *HuMemDirectMallocNum(HEAPID heap, s32 size, u32 num);
void *HuMemDirectTailMalloc(HEAPID heap, s32 size);
void HuMemDirectFree(void *ptr);
void HuMemDirectFreeNum(HEAPID heap, u32 num);
s32 HuMemUsedMallocSizeGet(HEAPID heap);
s32 HuMemUsedMallocBlockGet(HEAPID heap);
u32 HuMemHeapSizeGet(HEAPID heap);
void *HuMemHeapPtrGet(HEAPID heap);
void *HuMemRecoveryHeapGet(void);

void *HuMemHeapInit(void *heap, s32 size);
void *HuMemMemoryAlloc(void *heap, s32 size, u32 retAddr);
void *HuMemMemoryAllocNum(void *heap, s32 size, u32 num, u32 retAddr);
void *HuMemTailMemoryAlloc(void *heap, s32 size, u32 retAddr);

void HuMemMemoryFree(void *heap, u32 retAddr);
void HuMemMemoryFreeNum(void *heap, u32 num, u32 retAddr);
s32 HuMemUsedMemorySizeGet(void *heap);
s32 HuMemUsedMemoryBlockGet(void *heap);
s32 HuMemMemorySizeGet(void *heap);
s32 HuMemMemoryAllocSizeGet(s32 size);
s32 HuMemMaxMemorySizeGet(void *heap);

#ifdef __cplusplus
};
#endif

#endif