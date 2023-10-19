
// TEM QUE SER PEQUENO
// SE NAO JA COMECA CRIANDO MUITOS PATHS, E QUANTO MAIS PATHS, MAIS CHANCES TEM DE QUEBRAR A IDEIA
//  EX.: APOS REGISTRAR MUITOS, TENTAR REGISTRAR UM "ZZZZZZZZZZZ" (HASH 0xFFFFFFFFFFFFFFFF) -> SERA O PRIMEIRO DO TAL PATH
// TAMBEM NAO EH COMUM HASHES DE POUCOS BITS, POR EXEMPLO 0
typedef u8  tree8x16_len_t;
typedef u8  tree8x64_len_t;
typedef u16 tree16x32_len_t;
typedef u16 tree16x64_len_t;
typedef u32 tree32x64_len_t;
typedef u32 tree32x128_len_t;
typedef u64 tree64x128_len_t;

typedef u16 tree8x16_hash_t;
typedef u64 tree8x64_hash_t;
typedef u32 tree16x32_hash_t;
typedef u64 tree16x64_hash_t;
typedef u64 tree32x64_hash_t;
typedef u64 tree32x128_hash_t;
typedef u64 tree64x128_hash_t;

#define TREE8x16_HASH_N   1
#define TREE8x64_HASH_N   1
#define TREE16x32_HASH_N  1
#define TREE16x64_HASH_N  1
#define TREE32x64_HASH_N  1
#define TREE32x128_HASH_N 2
#define TREE64x128_HASH_N 2

#define TREE8x16_SIZE   /*  8 */ ( 6*sizeof(tree8x16_len_t)   + TREE8x16_HASH_N  * sizeof(tree8x16_hash_t))
#define TREE8x64_SIZE   /* 16 */ ( 8*sizeof(tree8x64_len_t)   + TREE8x64_HASH_N  * sizeof(tree8x64_hash_t))
#define TREE16x32_SIZE  /* 16 */ ( 6*sizeof(tree16x32_len_t)  + TREE16x32_HASH_N * sizeof(tree16x32_hash_t))
#define TREE16x64_SIZE  /* 32 */ (12*sizeof(tree16x64_len_t)  + TREE16x64_HASH_N * sizeof(tree16x64_hash_t))
#define TREE32x64_SIZE  /* 32 */ ( 6*sizeof(tree32x64_len_t)  + TREE32x64_HASH_N * sizeof(tree32x64_hash_t))
#define TREE32x128_SIZE /* 32 */ ( 4*sizeof(tree32x128_len_t) + TREE32x128_HASH_N* sizeof(tree32x128_hash_t))
#define TREE64x128_SIZE /* 64 */ ( 6*sizeof(tree64x128_len_t) + TREE64x128_HASH_N* sizeof(tree64x128_hash_t))

#define TREE_CHILDS_N(T) ((TREE##T##_SIZE - TREE##T##_HASH_N * sizeof(tree_hash_t(T)))/sizeof(tree_len_t(T)))

#define tree_s(T)      tree##T##_s
#define tree_len_t(T)  tree##T##_len_t
#define tree_hash_t(T) tree##T##_hash_t

#define TREE_ARGS_DECL_8x16   const tree8x16_hash_t   a
#define TREE_ARGS_DECL_8x64   const tree8x64_hash_t   a
#define TREE_ARGS_DECL_16x32  const tree16x32_hash_t  a
#define TREE_ARGS_DECL_16x64  const tree16x64_hash_t  a
#define TREE_ARGS_DECL_32x64  const tree32x64_hash_t  a
#define TREE_ARGS_DECL_32x128 const tree32x128_hash_t a, const tree32x128_hash_t b
#define TREE_ARGS_DECL_64x128 const tree64x128_hash_t a, const tree64x128_hash_t b

#define TREE_ARGS_CALL_8x16   a
#define TREE_ARGS_CALL_8x64   a
#define TREE_ARGS_CALL_16x32  a
#define TREE_ARGS_CALL_16x64  a
#define TREE_ARGS_CALL_32x64  a
#define TREE_ARGS_CALL_32x128 a, b
#define TREE_ARGS_CALL_64x128 a, b

#define TREELOOKUP_HASH_8x16   u16 hash = a
#define TREELOOKUP_HASH_8x64   u64 hash = a
#define TREELOOKUP_HASH_16x32  u32 hash = a
#define TREELOOKUP_HASH_16x64  u64 hash = a
#define TREELOOKUP_HASH_32x64  u64 hash = a
#define TREELOOKUP_HASH_32x128 u64 hash = a + b
#define TREELOOKUP_HASH_64x128 u64 hash = a + b

#define TREELOOKUP_NODE_IS_8x16   node->hash[0] == a
#define TREELOOKUP_NODE_IS_8x64   node->hash[0] == a
#define TREELOOKUP_NODE_IS_16x32  node->hash[0] == a
#define TREELOOKUP_NODE_IS_16x64  node->hash[0] == a
#define TREELOOKUP_NODE_IS_32x64  node->hash[0] == a
#define TREELOOKUP_NODE_IS_32x128 node->hash[0] == a && node->hash[1] == b
#define TREELOOKUP_NODE_IS_64x128 node->hash[0] == a && node->hash[1] == b

#define TREELOOKUP_ASSIGN_8x16   node->hash[0] = a
#define TREELOOKUP_ASSIGN_8x64   node->hash[0] = a
#define TREELOOKUP_ASSIGN_16x32  node->hash[0] = a
#define TREELOOKUP_ASSIGN_16x64  node->hash[0] = a
#define TREELOOKUP_ASSIGN_32x64  node->hash[0] = a
#define TREELOOKUP_ASSIGN_32x128 node->hash[0] = a; node->hash[1] = b
#define TREELOOKUP_ASSIGN_64x128 node->hash[0] = a; node->hash[1] = b

#define TREELOOKUP_NODE_AND_HASH(T) tree_s(T)* node = tree; TREELOOKUP_HASH_##T
#define TREELOOKUP_PTR(T) tree_len_t(T)* const ptr = &node->childs[hash % TREE_CHILDS_N(T)]
#define TREELOOKUP_ID_FROM_PTR(T) const size_t id = *ptr
#define TREELOOKUP_ID_IS_END !id
#define TREELOOKUP_NODE_FROM_ID(T) node = &tree[id]
#define TREELOOKUP_HASH_NEXT(T) hash /= TREE_CHILDS_N(T)
#define TREELOOKUP_INSERT(T) tree##T##_insert(tree, ptr, TREE_ARGS_CALL_##T)
#define TREELOOKUP_NODE_ID (node - tree) - 1

#define TREE_HASHES(T, i) ((T)[1+(i)].hash)

#define _TREE(T)                                                                                                           \
typedef struct tree_s(T) {                                                                                                 \
            tree_len_t(T) childs[TREE_CHILDS_N(T)];                                                                        \
    union {                                                                                                                \
        struct { /* ROOT */                                                                                                \
            tree_len_t(T) count;                                                                                           \
            tree_len_t(T) size;                                                                                            \
        }; /* NODES */                                                                                                     \
            tree_hash_t(T) hash[TREE##T##_HASH_N];                                                                         \
    };                                                                                                                     \
} tree_s(T);                                                                                                               \
                                                                                                                           \
static inline size_t tree##T##_insert (tree_s(T)* const tree, tree_len_t(T)* const ptr, TREE_ARGS_DECL_##T) {              \
                                                                                                                           \
    /* LIMITA AO MAXIMO */                                                                                                 \
    if (tree->count == tree->size)                                                                                         \
        return tree->size;                                                                                               \
                                                                                                                           \
    /* PEGA O PROXIMO SLOT LIVRE */                                                                                        \
    tree_s(T)* const node = &tree[*ptr = ++(tree->count)];                                                                 \
                                                                                                                           \
    TREELOOKUP_ASSIGN_##T;                                                                                                 \
                                                                                                                           \
    return TREELOOKUP_NODE_ID;                                                                                             \
}                                                                                                                          \
                                                                                                                           \
/* PROCURA UM ITEM */                                                                                                      \
static inline size_t tree##T##_lookup (const tree_s(T)* const tree, TREE_ARGS_DECL_##T) {                                  \
    const TREELOOKUP_NODE_AND_HASH(T);                                                                                     \
    loop { const TREELOOKUP_PTR(T);                                                                                        \
        TREELOOKUP_ID_FROM_PTR(T);                                                                                         \
        if (TREELOOKUP_ID_IS_END)                                                                                          \
            return tree->size;                                                                                           \
        TREELOOKUP_NODE_FROM_ID(T);                                                                                        \
        if (TREELOOKUP_NODE_IS_##T)                                                                                        \
            return TREELOOKUP_NODE_ID;                                                                                     \
        TREELOOKUP_HASH_NEXT(T);                                                                                           \
    }                                                                                                                      \
}                                                                                                                          \
                                                                                                                           \
/* ADICIONA UM ITEM, OU PEGA O QUE JA TEM SE ELE JA EXISTE */                                                              \
static inline size_t tree##T##_lookup_add (tree_s(T)* const tree, TREE_ARGS_DECL_##T) {                                    \
    TREELOOKUP_NODE_AND_HASH(T);                                                                                           \
    loop { TREELOOKUP_PTR(T);                                                                                              \
        TREELOOKUP_ID_FROM_PTR(T);                                                                                         \
        if (TREELOOKUP_ID_IS_END)                                                                                          \
            return TREELOOKUP_INSERT(T);                                                                                   \
        TREELOOKUP_NODE_FROM_ID(T);                                                                                        \
        if (TREELOOKUP_NODE_IS_##T)                                                                                        \
            return TREELOOKUP_NODE_ID;                                                                                     \
        TREELOOKUP_HASH_NEXT(T);                                                                                           \
    }                                                                                                                      \
}                                                                                                                          \
                                                                                                                           \
/* ADICIONA UM ITEM, SEM SE IMPORTAR SE ELE JA EXISTE */                                                                   \
static inline size_t tree##T##_add_multiple (tree_s(T)* const tree, TREE_ARGS_DECL_##T) {                                  \
    TREELOOKUP_NODE_AND_HASH(T);                                                                                           \
    loop { TREELOOKUP_PTR(T);                                                                                              \
        TREELOOKUP_ID_FROM_PTR(T);                                                                                         \
        if (TREELOOKUP_ID_IS_END)                                                                                          \
            return TREELOOKUP_INSERT(T);                                                                                   \
        TREELOOKUP_HASH_NEXT(T);                                                                                           \
    }                                                                                                                      \
}                                                                                                                          \
                                                                                                                           \
/* ADICIONA UM ITEM, MAS ERRO SE ELE JA EXISTE */                                                                          \
static inline size_t tree##T##_add_single (tree_s(T)* const tree, TREE_ARGS_DECL_##T) {                                    \
    TREELOOKUP_NODE_AND_HASH(T);                                                                                           \
    loop { TREELOOKUP_PTR(T);                                                                                              \
        TREELOOKUP_ID_FROM_PTR(T);                                                                                         \
        if (TREELOOKUP_ID_IS_END)                                                                                          \
            return TREELOOKUP_INSERT(T);                                                                                   \
        TREELOOKUP_NODE_FROM_ID(T);                                                                                        \
        if (TREELOOKUP_NODE_IS_##T)                                                                                        \
            return tree->size;                                                                                           \
        TREELOOKUP_HASH_NEXT(T);                                                                                           \
    }                                                                                                                      \
}                                                                                                                          \
                                                                                                                           \
static inline tree_s(T)* tree##T##_realloc (tree_s(T)* const old, const size_t size, tree_s(T)* new) {                     \
                                                                                                                           \
    const size_t totalOld = (1 + old->count) * sizeof(tree_s(T));                                                          \
    const size_t totalNew = (1 + size)       * sizeof(tree_s(T));                                                          \
                                                                                                                           \
    ASSERT(totalOld <= totalNew);                                                                                          \
                                                                                                                           \
    if (new == NULL)                                                                                                       \
        new = malloc(totalNew);                                                                                            \
    /* COPIA O VELHO */                                                                                                    \
    copy(new, old, totalOld);                                                                                              \
    /* LIMPA O RESTANTE */                                                                                                 \
    clear(new + totalOld, totalNew - totalOld);                                                                            \
    /* SE LIVRA DO VELHO */                                                                                                \
    free(old);                                                                                                             \
                                                                                                                           \
    return new;                                                                                                            \
}                                                                                                                          \
                                                                                                                           \
/* NOTE: JA FAZ ISSO AQUI PARA QUE AS DEMAIS FUNCOES SEJAM MAIS SIMPLES */                                                 \
/*      tree->count = 0; */                                                                                                \
/*      tree[*].childs[*] = 0; */                                                                                          \
static inline tree_s(T)* tree##T##_new (const size_t size, tree_s(T)* tree) {                                              \
                                                                                                                           \
    ASSERT(TREE##T##_SIZE == sizeof(tree_s(T)));                                                                           \
                                                                                                                           \
    const size_t total = (1 + size) * sizeof(tree_s(T));                                                                   \
                                                                                                                           \
    if (tree == NULL)                                                                                                      \
        tree = malloc(total);                                                                                              \
                                                                                                                           \
    clear(tree, total);                                                                                                    \
                                                                                                                           \
    tree->size = size;                                                                                                     \
                                                                                                                           \
    return tree;                                                                                                           \
}                                                                                                                          \

// TODO: FIXME: UMA FUNCAO PARA A PARTIR DO ID X, PROCURAR O PROXIMO COM TAL HASH
// PODE PRECISAR DE UMA FUNCAO HELPER ITERATOR PARA SALVAR O HASH, CUR ID E ESTTAS VARIAVEIS
_TREE(8x16)
_TREE(8x64)
_TREE(16x32)
_TREE(16x64)
_TREE(32x64)
_TREE(32x128)
_TREE(64x128)
