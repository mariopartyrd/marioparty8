#include "game/memory.h"
#include "game/init.h"
#include <revolution.h>

typedef struct HeapSize_s {
	BOOL isMem2;
	u32 size;
} HEAPSIZE;

static HEAPSIZE HeapSizeTbl[HEAP_MAX+1] = {
	{ FALSE, 0x400000 }, //HEAP_HEAP
	{ TRUE, 0x600000 }, //HEAP_HEAP2
	{ TRUE, 0x1600000 }, //HEAP_AUDIO
	{ FALSE, 0x1000000 }, //HEAP_MODEL
	{ TRUE, 0x500000 }, //HEAP_RECOVERY
	{ TRUE, 0xFE0000 }, //HEAP_DVD
	{ TRUE, 0x1C0000 }, //HEAP_SPACE
};

static void *HeapTbl[HEAP_MAX];

static void *RecoveryHeap;

void HuMemInitAll(void)
{
	int i;
	u32 freeSize;
	void *heap;
	for(i=0; i<HEAP_MAX; i++) {
		OSReport("%d:MEM1 Left %x \n", i, MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM1));
		if(currentHeapHandleMEM2) {
			OSReport(" MEM2 Left %x\n", MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM2));
		}
		if(!HeapSizeTbl[i].isMem2) {
			heap = MEMAllocFromExpHeapEx(currentHeapHandleMEM1, HeapSizeTbl[i].size, 32);
			if(heap == NULL) {
				OSReport("HuMem> Failed MEM1 Alloc Size:%x(left:%x)\n", HeapSizeTbl[i].size, MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM1));
				return;
			}
		} else {
			heap = MEMAllocFromExpHeapEx(currentHeapHandleMEM2, HeapSizeTbl[i].size, 32);
			if(heap == NULL) {
				OSReport("HuMem> Failed MEM2 Alloc Size:%x(left:%x)\n", HeapSizeTbl[i].size, MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM2));
				return;
			}
		}
		HeapTbl[i] = HuMemInit(heap, HeapSizeTbl[i].size);
	}
	if(currentHeapHandleMEM1) {
		freeSize = MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM1);
		OSReport("HuMem 1> left memory space %dKB(%d)\n", freeSize/1024, freeSize);
	}
	if(currentHeapHandleMEM2) {
		freeSize = MEMGetTotalFreeSizeForExpHeap(currentHeapHandleMEM2);
		OSReport("HuMem 2> left memory space %dKB(%d)\n", freeSize/1024, freeSize);
	}
	RecoveryHeap = HeapTbl[HEAP_RECOVERY];
}

void *HuMemInit(void *heap, u32 size)
{
	return HuMemHeapInit(heap, size);
}

void HuMemDCFlushAll(void)
{
	HuMemDCFlush(HEAP_MODEL);
	HuMemDCFlush(HEAP_HEAP);
}

void HuMemDCFlush(HEAPID heapId)
{
	DCFlushRangeNoSync(HeapTbl[heapId], HeapSizeTbl[heapId].size);
}

void *HuMemDirectMalloc(HEAPID heap, s32 size)
{
    register u32 retaddr;
    asm {
        mflr retaddr
    }
    size = OSRoundUp32B(size);
    return HuMemMemoryAlloc(HeapTbl[heap], size, retaddr);
}

void *HuMemDirectMallocNum(HEAPID heap, s32 size, u32 num)
{
    register u32 retaddr;
    asm {
        mflr retaddr
    }
    size = OSRoundUp32B(size);
    return HuMemMemoryAllocNum(HeapTbl[heap], size, num, retaddr);
}

void *HuMemDirectTailMalloc(HEAPID heap, s32 size)
{
    register u32 retaddr;
    asm {
        mflr retaddr
    }
    size = OSRoundUp32B(size);
    return HuMemTailMemoryAlloc(HeapTbl[heap], size, retaddr);
}

void HuMemDirectFree(void *ptr)
{
    register u32 retaddr;
    asm {
        mflr retaddr
    }
    HuMemMemoryFree(ptr, retaddr);
}

void HuMemDirectFreeNum(HEAPID heap, u32 num)
{
    register u32 retaddr;
    asm {
        mflr retaddr
    }
    HuMemMemoryFreeNum(HeapTbl[heap], num, retaddr);
}

s32 HuMemUsedMallocSizeGet(HEAPID heap)
{
    return HuMemUsedMemorySizeGet(HeapTbl[heap]);
}

s32 HuMemUsedMallocBlockGet(HEAPID heap)
{
    return HuMemUsedMemoryBlockGet(HeapTbl[heap]);
}

u32 HuMemHeapSizeGet(HEAPID heap)
{
    return HeapSizeTbl[heap].size;
}

void *HuMemHeapPtrGet(HEAPID heap)
{
    return HeapTbl[heap];
}

void *HuMemRecoveryHeapGet(void)
{
	return RecoveryHeap;
}