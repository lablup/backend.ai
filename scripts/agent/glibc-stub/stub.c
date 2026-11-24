/*
 * Empty on purpose: since glibc 2.34 the real implementations live in libc.so.6.
 * The linker drops a version node that has no symbol, so each node gets a placeholder.
 */
#define PLACEHOLDER(suffix) void __backendai_glibc_stub_##suffix(void) {}

PLACEHOLDER(2_2_5)
PLACEHOLDER(2_2_6)
PLACEHOLDER(2_3_2)
PLACEHOLDER(2_3_3)
PLACEHOLDER(2_3_4)
PLACEHOLDER(2_4)
PLACEHOLDER(2_5)
PLACEHOLDER(2_7)
PLACEHOLDER(2_11)
PLACEHOLDER(2_12)
PLACEHOLDER(2_17)
PLACEHOLDER(2_18)
PLACEHOLDER(2_28)
PLACEHOLDER(2_30)
PLACEHOLDER(2_31)
