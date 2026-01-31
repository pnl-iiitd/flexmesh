
#ifndef __GCM_DRIVER__
#define __GCM_DRIVER__
#include <stdio.h>
#include "bram_utils.h"
#include "dma_utils.h"
#include "xparameters.h"
#include "crypto_utils.h"
#include "xtime_l.h"

#define BYTE_FORMAT 8
#define TAG_SIZE 16
//#define AAD_MAX_SIZE 64
//#define IV_MAX_SIZE 64
//#define PT_SIZE 4000
#define KEY_SIZE 32
//#define CT_SIZE PT_SIZE
//#define AAD_SIZE 12
//#define IV_SIZE 12

#define AAD_SIZE 20
//#define IV_SIZE PT_SIZE

#define AES_DMA_ID_0 XPAR_HIER_0_AXI_DMA_0_DEVICE_ID
#define AES_DMA_ID_1 XPAR_AES_GCM_HIER_AES_GCM_DMA_DEVICE_ID

#define BRAM_ID_0 XPAR_AXI_BRAM_CTRL_0_DEVICE_ID
#define BRAM_ID_1 XPAR_AXI_BRAM_CTRL_1_DEVICE_ID
#define BRAM_ID_2 XPAR_AXI_BRAM_CTRL_2_DEVICE_ID
#define BRAM_ID_3 XPAR_AXI_BRAM_CTRL_3_DEVICE_ID

// Defining dma and bram instances
XAxiDma dma[XPAR_XAXIDMA_NUM_INSTANCES];
XBram bram[XPAR_XBRAM_NUM_INSTANCES];




uint8_t key[32]={0xfe,0xff,0xe9,0x92,0x86,0x65,0x73,0x1c,0x6d,0x6a,0x8f,0x94,0x67,0x30,0x83,0x08,
	                  0xfe,0xff,0xe9,0x92,0x86,0x65,0x73,0x1c,0x6d,0x6a,0x8f,0x94,0x67,0x30,0x83,0x08};
//
//uint8_t IV[PT_SIZE]={0x93,0x13,0x22,0x5d,0xf8,0x84,0x06,0xe5,0x55,0x90,0x9c,0x5a,0xff,0x52,0x69,0xaa,
//		  0x6a,0x7a,0x95,0x38,0x53,0x4f,0x7d,0xa1,0xe4,0xc3,0x03,0xd2,0xa3,0x18,0xa7,0x28,
//		  0xc3,0xc0,0xc9,0x51,0x56,0x80,0x95,0x39,0xfc,0xf0,0xe2,0x42,0x9a,0x6b,0x52,0x54,
//		  0x16,0xae,0xdb,0xf5,0xa0,0xde,0x6a,0x57,0xa6,0x37,0xb3,0x9b};
//
//uint8_t PT[PT_SIZE]={0xd9,0x31,0x32,0x25,0xf8,0x84,0x06,0xe5,0xa5,0x59,0x09,0xc5,0xaf,0xf5,0x26,0x9a,
//		  0x86,0xa7,0xa9,0x53,0x15,0x34,0xf7,0xda,0x2e,0x4c,0x30,0x3d,0x8a,0x31,0x8a,0x72,
//		  0x1c,0x3c,0x0c,0x95,0x95,0x68,0x09,0x53,0x2f,0xcf,0x0e,0x24,0x49,0xa6,0xb5,0x25,
//		  0xb1,0x6a,0xed,0xf5,0xaa,0x0d,0xe6,0x57,0xba,0x63,0x7b,0x39};
//
uint8_t AAD[20]={0xfe,0xed,0xfa,0xce,0xde,0xad,0xbe,0xef,0xfe,0xed,0xfa,0xce,0xde,0xad,0xbe,0xef,
	                  0xab,0xad,0xda,0xd2};

#define w1 0.5
#define w2 0.2
#define w3 0.2
#define w4 0.1

int pkt_size[12]={64, 128,256, 512, 1024, 1456, 2048, 4096, 5120, 6144, 7168, 8000};
int latency_1x1[12] = {3.86, 4.66, 6.032, 8.971, 14.58, 19.31, 25.97, 48.56, 59.75, 70.73, 81.69, 90.71};
int latency_1x4[12] = {3.894, 4.429, 5.232, 7.085, 10.584, 13.362, 17.545, 31.445, 38.209, 45.079, 51.998, 57.107};
int power_usage[2] = {4.35, 7.11};
int bram_usage[2] = {43.00, 43.00};
int lut_usage[2] = {17.00, 43.00};


#define ITERATIONS 499

//float overall_time_accumulation_=0, overall_time[ITERATIONS]={0};
int overall_time_accumulation_=0, overall_time[ITERATIONS]={0};



typedef struct
{
	uint8_t PTlenbits[BYTE_FORMAT];
	uint8_t AADlenbits[BYTE_FORMAT];
	uint8_t IVlenbits[BYTE_FORMAT];
	uint8_t Tlenbits[BYTE_FORMAT];
	uint8_t* PT;
	int PT_SIZE;
//
//	uint8_t AAD_SIZE=20;
//	uint8_t AAD[AAD_SIZE]={0xfe,0xed,0xfa,0xce,0xde,0xad,0xbe,0xef,0xfe,0xed,0xfa,0xce,0xde,0xad,0xbe,0xef,
//            0xab,0xad,0xda,0xd2};;

	uint8_t *IV;
	int IV_SIZE;

	uint8_t* CT;
	int CT_SIZE;
	uint8_t TAG[TAG_SIZE];

	uint8_t IP;

	uint32_t input_size;
	uint32_t output_size;
} ctx_t;

void calculate_score(ctx_t * ctx, int size){
    // score = w1*(latency)+w2*(LUT)+w3*(BRAM)+w4*(Power)
//	int minDiff = 10000000;
//	int nearestNeighbor = 0;
//
//	for (int i = 0; i < 12; ++i) {
//	    int diff = abs(pkt_size[i] - ctx->PT_SIZE);
//	    if (diff < minDiff) {
//	        minDiff = diff;
//	        nearestNeighbor = i;
//	     }
//	}
//
//    int score_1x1 = 0;
//    score_1x1=w1*latency_1x1[nearestNeighbor]+w2*lut_usage[0]+w3*bram_usage[0]+w4*power_usage[0];
//    int score_1x4 = w1*latency_1x4[nearestNeighbor]+w2*lut_usage[1]+w3*bram_usage[1]+w4*power_usage[1];
////    int score_1x4=0;
//    printf("%d\n",score_1x1);
//    printf("%d\n",score_1x4);
//    printf("%d\n", nearestNeighbor);
//    if(score_1x1<score_1x4){
//        printf("1x1 is better");
//        ctx->IP=0;
//    }
//    else{
//        printf("1x8 is better");
//        ctx->IP=2;
//    }
//	printf("%d\n", size);

	    if(size<512){
	        printf("Using 1x1\n");
	        ctx->IP=0;
	    }
	    else{
	        printf("Using 1x4\n");
	        ctx->IP=2;
	    }
}

void InitSystem()
{
    InitDMA(AES_DMA_ID_0, &dma[AES_DMA_ID_0]);
//    InitDMA(AES_DMA_ID_1, &dma[AES_DMA_ID_1]);
    InitBRAM(BRAM_ID_0, &bram[BRAM_ID_0]);
    InitBRAM(BRAM_ID_1, &bram[BRAM_ID_1]);
//    InitBRAM(BRAM_ID_2, &bram[BRAM_ID_2]);
//    InitBRAM(BRAM_ID_3, &bram[BRAM_ID_3]);
}

void InitRandPkt(ctx_t *ctx,int size)
{

    ctx->PT_SIZE = size;
    ctx->CT_SIZE = size;
//    ctx->IV_SIZE = size;
    ctx->IV_SIZE = 12;

	WPA_PUT_BE64(ctx->PTlenbits, ctx->PT_SIZE*8);
	WPA_PUT_BE64(ctx->AADlenbits, AAD_SIZE*8);
	WPA_PUT_BE64(ctx->IVlenbits, ctx->IV_SIZE*8);
	WPA_PUT_BE64(ctx->Tlenbits, TAG_SIZE*8);

    ctx->PT=(uint8_t *)malloc(ctx->PT_SIZE * sizeof(uint8_t));
    ctx->CT=(uint8_t *)malloc(ctx->CT_SIZE * sizeof(uint8_t));
    ctx->IV=(uint8_t *)malloc(ctx->IV_SIZE * sizeof(uint8_t));


	for(int i = 0; i < ctx->PT_SIZE; i++){
		ctx->PT[i]=i;

	}

	for(int i = 0; i < ctx->IV_SIZE; i++){
		ctx->IV[i]=i;
	}
	WPA_PUT_BE64(ctx->AADlenbits, AAD_SIZE*8);
	for(int i = 0; i < AAD_SIZE; i++){
		AAD[i]=i;
	}
//	calculate_score(ctx,size);

}




void InitCtx(ctx_t *ctx, int size){
	InitRandPkt(ctx,size);
	ctx->input_size = BYTE_FORMAT+BYTE_FORMAT+ BYTE_FORMAT+ROUND_TO_MUL_OF_X(ctx->PT_SIZE, 16) + ROUND_TO_MUL_OF_X(AAD_SIZE, 16) + ROUND_TO_MUL_OF_X(ctx->IV_SIZE, 16)+ KEY_SIZE+BYTE_FORMAT;
	ctx->output_size = ROUND_TO_MUL_OF_X(ctx->CT_SIZE, 16) + TAG_SIZE;
}

void WritePktToBRAM(ctx_t *ctx, int index){

	int offset = 0;
	WriteToBRAM(&bram[index], ctx->IVlenbits, BYTE_FORMAT, offset);
	offset += BYTE_FORMAT;


	WriteToBRAM(&bram[index], ctx->PTlenbits, BYTE_FORMAT, offset);
	offset +=BYTE_FORMAT;


	WriteToBRAM(&bram[index], ctx->AADlenbits, BYTE_FORMAT, offset);
	offset += BYTE_FORMAT;

	offset += (BYTE_FORMAT - 1);
	WriteToBRAM(&bram[index], ctx->Tlenbits, 1, offset);
	offset += 1;


	WriteToBRAM(&bram[index], ctx->IV, ctx->IV_SIZE, offset);
	offset += ROUND_TO_MUL_OF_X(ctx->IV_SIZE,16);

	WriteToBRAM(&bram[index], ctx->PT, ctx->PT_SIZE ,offset);
	offset += ROUND_TO_MUL_OF_X(ctx->PT_SIZE,16);



	WriteToBRAM(&bram[index], AAD, AAD_SIZE, offset);
	offset += ROUND_TO_MUL_OF_X(AAD_SIZE,16);


	WriteToBRAM(&bram[index], key, KEY_SIZE, offset);
}

void print_all(ctx_t* ctx){

		for(int i=0; i<BYTE_FORMAT; i++){
			printf("%d ", ctx->IVlenbits[i]);
		}
		printf("\n");
		printf("\n");

			printf("PTlenbits:\n ");
			for(int i=0; i<BYTE_FORMAT; i++){
				printf("%d ", ctx->PTlenbits[i]);
			}
			printf("\n");
			printf("\n");

		printf("AADlenbits:\n ");
		for(int i=0; i<BYTE_FORMAT; i++){
			printf("%d ", ctx->AADlenbits[i]);
		}
		printf("\n");
		printf("\n");

		printf("AADlenbits:\n ");
		for(int i=0; i<BYTE_FORMAT; i++){
			printf("%d ", ctx->Tlenbits[i]);
		}
		printf("\n");

		printf("IV:\n ");
		for(int i=0; i<ctx->IV_SIZE; i++){
			printf("%0x ", ctx->IV[i]);
		}
		printf("\n");
		printf("\n");
		printf("pt:\n ");
		for(int i=0; i<ctx->PT_SIZE; i++){
			printf("%0x ", ctx->PT[i]);
		}
		printf("\n");
		printf("\n");

		printf("AAD:\n ");
		for(int i=0; i<AAD_SIZE; i++){
			printf("%0x ", AAD[i]);
		}
		printf("\n");
		printf("\n");


		printf("KEY:\n ");
		for(int i=0; i<KEY_SIZE; i++){
			printf("%0x ", key[i]);
		}
		printf("\n");
		printf("\n");
		printf("%d\n",ctx->input_size);
		printf("%d\n",ctx->output_size);
		printf("\n");
}

uint8_t *out_addr_0;
uint8_t *out_addr_0_1;

void prints_blocks(uint8_t X[], int lim)
	{
	    printf("\n");
	    for (int i = 0; i < lim; i++)
	    {
	        if (X[i] == 0)
	            printf("00");
	        else if (X[i] < 16)
	            printf("0%x", X[i]);
	        else
	            printf("%x", X[i]);
	        if (i != 0 && (i + 1) % 16 == 0)
	            printf("\n");
	    }
	}




void ProcessPkt(ctx_t *ctx,int DMA_index_1_1, int bram_input_index_1_1, int bram_output_index_1_1,int iteration_index){

		uint8_t *bram_addr_0 = GetBRAMBaseAddr(&bram[bram_input_index_1_1]);
		out_addr_0 = GetBRAMBaseAddr(&bram[bram_output_index_1_1]);


		XTime start, end;
		XTime_GetTime(&start);
		TransferToDevice(&dma[DMA_index_1_1], (UINTPTR) bram_addr_0, ctx->input_size);
		TransferToMem(&dma[DMA_index_1_1], (UINTPTR) out_addr_0, ctx->output_size);

		WaitForDevTransfer(&dma[DMA_index_1_1]);
		WaitForMemTransfer(&dma[DMA_index_1_1]);

		XTime_GetTime(&end);
		overall_time_accumulation_+=(end-start);
		overall_time[iteration_index]=(end-start);



//		overall_time[iteration_index]=((float)(end-start)/COUNTS_PER_SECOND);

//		printf("1_1 pkt size: %d is %f\n",ctx->PT_SIZE, overall_time[iteration_index]);


}
#endif
