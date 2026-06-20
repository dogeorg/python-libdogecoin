/* AUTO-GENERATED from the fetched libdogecoin header. */
void dogecoin_ecc_start(void);
void dogecoin_ecc_stop(void);
int generatePrivPubKeypair(char* wif_privkey, char* p2pkh_pubkey, int is_testnet);
int generateHDMasterPubKeypair(char* wif_privkey_master, char* p2pkh_pubkey_master, int is_testnet);
int generateDerivedHDPubkey(const char* wif_privkey_master, char* p2pkh_pubkey);
int verifyPrivPubKeypair(char* wif_privkey, char* p2pkh_pubkey, int is_testnet);
int verifyHDMasterPubKeypair(char* wif_privkey_master, char* p2pkh_pubkey_master, int is_testnet);
int verifyP2pkhAddress(char* p2pkh_pubkey, size_t len);
int start_transaction(void);
int add_utxo(int txindex, char* hex_utxo_txid, int vout);
int add_output(int txindex, char* destinationaddress, char* amount);
char* finalize_transaction(int txindex, char* destinationaddress, char* subtractedfee, char* out_dogeamount_for_verification, char* changeaddress);
int sign_transaction(int txindex, char* script_pubkey, char* privkey);
void remove_all(void);
char* get_raw_transaction(int txindex);
void clear_transaction(int txindex);
int sign_raw_transaction(int inputindex, char* incomingrawtx, char* scripthex, int sighashtype, char* privkey);
int store_raw_transaction(char* incomingrawtx);
