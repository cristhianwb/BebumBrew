#include "./crc.h"


crc crcFast(uint8_t* message, int nBytes){
    uint8_t data;
    crc remainder = 0;
    int byte;

    /*
     * Divide the message by the polynomial, a byte at a time.
     */
    for (byte = 0; byte < nBytes; ++byte)
    {
        data = message[byte] ^ (remainder >> (WIDTH - 8));
        remainder = pgm_read_byte(&crcTable[data]) ^ (remainder << 8);
    }

    /*
     * The final remainder is the CRC.
     */
    return (remainder);

}

