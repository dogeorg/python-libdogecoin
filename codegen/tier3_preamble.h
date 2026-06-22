/* Tier 3 cdef preamble — hand-curated struct layouts and handle APIs.
 *
 * cffi needs concrete struct definitions (macros resolved to integer literals)
 * to allocate dogecoin_hdnode and read its fields. Chain parameters are passed
 * as opaque void* handles obtained from helper accessors (cffi cannot expose
 * an extern const struct global directly), defined in the set_source C body.
 *
 * Sizes mirror libdogecoin.h: chaincode 32, privkey 32, pubkey 33.
 */

/* HD (BIP32) node — transparent so cffi can allocate it and read its fields. */
typedef struct {
    uint32_t depth;
    uint32_t fingerprint;
    uint32_t child_num;
    uint8_t chain_code[32];
    uint8_t private_key[32];
    uint8_t public_key[33];
} dogecoin_hdnode;

/* chain parameter accessors — return opaque pointers to the library globals */
void* dogecoin_chainparams_main_ptr(void);
void* dogecoin_chainparams_test_ptr(void);
void* dogecoin_chainparams_regtest_ptr(void);

dogecoin_hdnode* dogecoin_hdnode_new(void);
dogecoin_hdnode* dogecoin_hdnode_copy(const dogecoin_hdnode* hdnode);
void dogecoin_hdnode_free(dogecoin_hdnode* node);
int dogecoin_hdnode_public_ckd(dogecoin_hdnode* inout, uint32_t i);
int dogecoin_hdnode_from_seed(const uint8_t* seed, int seed_len, dogecoin_hdnode* out);
int dogecoin_hdnode_private_ckd(dogecoin_hdnode* inout, uint32_t i);
void dogecoin_hdnode_fill_public_key(dogecoin_hdnode* node);
void dogecoin_hdnode_serialize_public(const dogecoin_hdnode* node, const void* chain, char* str, size_t strsize);
void dogecoin_hdnode_serialize_private(const dogecoin_hdnode* node, const void* chain, char* str, size_t strsize);
int dogecoin_hdnode_get_pub_hex(const dogecoin_hdnode* node, char* str, size_t* strsize);
int dogecoin_hdnode_deserialize(const char* str, const void* chain, dogecoin_hdnode* node);

/* --- Layer B: key / pubkey objects (cleanse-on-exit) --------------------- */
/* Both structs are caller-allocated (init/cleanse, not new/free). Transparent
 * so cffi can allocate them and read fields. Sizes from dogecoin.h:
 *   privkey 32, pubkey uncompressed 65, compressed 33. */
typedef struct {
    uint8_t privkey[32];
} dogecoin_key;

typedef struct {
    uint8_t compressed;      /* dogecoin_bool = uint8_t */
    uint8_t pubkey[65];
} dogecoin_pubkey;

/* key lifecycle */
void dogecoin_privkey_init(dogecoin_key* privkey);
int dogecoin_privkey_is_valid(const dogecoin_key* privkey);
void dogecoin_privkey_cleanse(dogecoin_key* privkey);
int dogecoin_privkey_gen(dogecoin_key* privkey);
int dogecoin_privkey_verify_pubkey(dogecoin_key* privkey, dogecoin_pubkey* pubkey);

/* key <-> WIF (bridges to the Tier 1 string world), chain as opaque void* */
void dogecoin_privkey_encode_wif(const dogecoin_key* privkey, const void* chain, char* privkey_wif, size_t* strsize_inout);
int dogecoin_privkey_decode_wif(const char* privkey_wif, const void* chain, dogecoin_key* privkey);

/* pubkey lifecycle + ops */
void dogecoin_pubkey_init(dogecoin_pubkey* pubkey);
int dogecoin_pubkey_is_valid(const dogecoin_pubkey* pubkey);
void dogecoin_pubkey_cleanse(dogecoin_pubkey* pubkey);
void dogecoin_pubkey_from_key(const dogecoin_key* privkey, dogecoin_pubkey* pubkey_inout);
void dogecoin_pubkey_get_hash160(const dogecoin_pubkey* pubkey, uint8_t* hash160);
int dogecoin_pubkey_get_hex(const dogecoin_pubkey* pubkey, char* str, size_t* strsize);

/* sign / verify (hash is uint256_t == uint8_t[32]) */
int dogecoin_key_sign_hash(const dogecoin_key* privkey, const uint8_t* hash, unsigned char* sigout, size_t* outlen);
int dogecoin_pubkey_verify_sig(const dogecoin_pubkey* pubkey, const uint8_t* hash, unsigned char* sigder, size_t len);
