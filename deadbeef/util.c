
/* */
#define ALIGNMENT 4096

#define ALIGNED(x) ((((x) + ALIGNMENT - 1)/ALIGNMENT) * ALIGNMENT)

static inline void* malloc_aligned (const size_t size) {

	const size_t aligned = ALIGNED(size);

	void* const buff = aligned_alloc(ALIGNMENT, aligned);

	memset(buff + size, 0, aligned - size);

	return buff;
}
