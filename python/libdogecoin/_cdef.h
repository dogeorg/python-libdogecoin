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
    ...;
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
    ...;
} dogecoin_key;

typedef struct {
    uint8_t compressed;      /* dogecoin_bool = uint8_t */
    uint8_t pubkey[65];
    ...;
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

/* AUTO-GENERATED from the fetched libdogecoin header. */
int chain_from_b58_prefix_bool(char* address);
void dogecoin_ecc_start(void);
void dogecoin_ecc_stop(void);
int isTestnetFromB58Prefix(char* address);
int isMainnetFromB58Prefix(char* address);
int generatePrivPubKeypair(char* wif_privkey, char* p2pkh_pubkey, int is_testnet);
int generateHDMasterPubKeypair(char* hd_privkey_master, char* p2pkh_pubkey_master, int is_testnet);
int generateDerivedHDPubkey(char* hd_privkey_master, char* p2pkh_pubkey);
int verifyPrivPubKeypair(char* wif_privkey, char* p2pkh_pubkey, int is_testnet);
int verifyHDMasterPubKeypair(char* hd_privkey_master, char* p2pkh_pubkey_master, int is_testnet);
int verifyP2pkhAddress(char* p2pkh_pubkey, size_t len);
int getDerivedHDAddress(char* masterkey, uint32_t account, int ischange, uint32_t addressindex, char* outaddress, int outprivkey);
int getDerivedHDAddressByPath(char* masterkey, char* derived_path, char* outaddress, int outprivkey);
int getAddressFromPubkey(char* pubkey_hex, int is_testnet, char* p2pkh_address);
int getPubkeyFromPrivkey(char* privkey_wif, int is_testnet, char* pubkey_hex, size_t* sizeout);
int genPrivkey(int is_testnet, char* privkey_wif, size_t strsize_wif, char* privkey_hex);
int dogecoin_p2pkh_address_to_pubkey_hash(char* p2pkh, char* scripthash);
char* dogecoin_address_to_pubkey_hash(char* p2pkh);
char* dogecoin_private_key_wif_to_pubkey_hash(char* private_key_wif);
int getAddrFromPubkeyHash(char* pubkey_hash, int is_testnet, char* p2pkh_address);
void getWifEncodedPrivKey(char* privkey, int is_testnet, char* privkey_wif, size_t* strsize_wif);
int getDecodedPrivKeyWif(char* privkey_wif, int is_testnet, char* privkey_hex);
int getHDRootKeyFromSeed(uint8_t* seed, const int seed_len, int is_testnet, char* masterkey);
int getHDPubKey(char* hdkey, int is_testnet, char* hdpubkey);
int deriveExtKeyFromHDKey(char* extkey, char* keypath, int is_testnet, char* key);
int deriveExtPubKeyFromHDKey(char* extpubkey, char* keypath, int is_testnet, char* pubkey);
int genHDMaster(int is_testnet, char* masterkey, size_t strsize);
int printNode(int is_testnet, char* nodeser);
int deriveHDExtFromMaster(int is_testnet, char* masterkey, char* keypath, char* extkeyout, size_t extkeyout_size);
char* getHDNodePrivateKeyWIFByPath(char* masterkey, char* derived_path, char* outaddress, int outprivkey);
int deriveBIP44ExtendedKey(char* hd_privkey_master, const uint32_t* account, char* change_level, const uint32_t* address_index, char* path, char* extkeyout, char* keypath);
int deriveBIP44ExtendedPublicKey(char* hd_privkey_master, const uint32_t* account, char* change_level, const uint32_t* address_index, char* path, char* extkeyout, char* keypath);
char* utils_uint8_to_hex(const uint8_t* bin, size_t l);
int generateEnglishMnemonic(char* entropy, char* size, char* mnemonic);
int generateRandomEnglishMnemonic(char* size, char* mnemonic);
int dogecoin_seed_from_mnemonic(char* mnemonic, char* pass, uint8_t* seed);
int getDerivedHDAddressFromMnemonic(const uint32_t account, const uint32_t index, char* change_level, char* mnemonic, char* pass, char* p2pkh_pubkey, int is_testnet);
int start_transaction(void);
int add_utxo(int txindex, char* hex_utxo_txid, int vout);
int add_output(int txindex, char* destinationaddress, char* amount);
char* finalize_transaction(int txindex, char* destinationaddress, char* subtractedfee, char* out_dogeamount_for_verification, char* changeaddress);
int sign_transaction(int txindex, char* script_pubkey, char* privkey);
int sign_transaction_w_privkey(int txindex, int vout_index, char* privkey);
void remove_all(void);
char* get_raw_transaction(int txindex);
void clear_transaction(int txindex);
int qrgen_p2pkh_to_qrbits(const char* in_p2pkh, uint8_t* outQrByteArray);
int qrgen_p2pkh_to_qr_string(const char* in_p2pkh, char* outString);
void qrgen_p2pkh_consoleprint_to_qr(char* in_p2pkh);
int qrgen_string_to_qr_pngfile(const char* outFilename, const char* inString, uint8_t sizeMultiplier);
int qrgen_string_to_qr_jpgfile(const char* outFilename, const char* inString, uint8_t sizeMultiplier);
int sign_raw_transaction(int inputindex, char* incomingrawtx, char* scripthex, int sighashtype, char* privkey);
int store_raw_transaction(char* incomingrawtx);
int koinu_to_coins_str(uint64_t koinu, char* str);
uint64_t coins_to_koinu_str(char* coins);
int start_key(void);
char* sign_message(char* privkey, char* msg);
int verify_message(char* sig, char* msg, char* address);
