<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const metadata = ref({ pages: [], series: [], teams: [], positions: [] })
const pageKey = ref('')
const seriesCode = ref('0')
const season = ref('')
const records = ref([])
const total = ref(0)
const offset = ref(0)
const limit = ref(100)
const loading = ref(false)
const error = ref('')

const selectedPage = computed(() => metadata.value.pages.find((page) => page.key === pageKey.value))
const seasons = computed(() => {
  if (!selectedPage.value) return []
  const values = []
  for (let year = selectedPage.value.seasonEnd; year >= selectedPage.value.seasonStart; year -= 1) {
    values.push(year)
  }
  return values
})

const columns = computed(() => {
  const first = records.value[0]
  return first?.columns || []
})

const pageLabel = (page) => {
  const group = page.recordGroup === 'player' ? '선수' : '팀'
  const categoryMap = {
    hitter: '타자',
    pitcher: '투수',
    defense: '수비',
    runner: '주루',
  }
  return `${group} ${categoryMap[page.category] || page.category} ${page.pageKind}`
}

const fetchMetadata = async () => {
  const response = await fetch(`${API_BASE_URL}/metadata`)
  if (!response.ok) throw new Error('메타데이터를 불러오지 못했습니다.')
  metadata.value = await response.json()
  if (!pageKey.value && metadata.value.pages.length) {
    pageKey.value = metadata.value.pages[0].key
  }
}

const fetchRecords = async () => {
  if (!pageKey.value || !season.value) return
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({
      page_key: pageKey.value,
      series_code: seriesCode.value,
      season: season.value,
      limit: String(limit.value),
      offset: String(offset.value),
    })
    const response = await fetch(`${API_BASE_URL}/records?${params}`)
    if (!response.ok) throw new Error('기록 데이터를 불러오지 못했습니다.')
    const payload = await response.json()
    records.value = payload.rows
    total.value = payload.total
  } catch (err) {
    error.value = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
    records.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const nextPage = () => {
  if (offset.value + limit.value >= total.value) return
  offset.value += limit.value
}

const previousPage = () => {
  offset.value = Math.max(0, offset.value - limit.value)
}

watch(selectedPage, (page) => {
  if (!page) return
  season.value = String(page.seasonEnd)
  offset.value = 0
})

watch([pageKey, seriesCode, season, offset, limit], fetchRecords)

onMounted(async () => {
  try {
    await fetchMetadata()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'API 서버에 연결하지 못했습니다.'
  }
})
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <h1>KBO Records</h1>
        <p>MySQL에 적재된 KBO 기록실 데이터를 조회합니다.</p>
      </div>
      <div class="status" :class="{ muted: !total }">
        {{ total.toLocaleString() }} rows
      </div>
    </header>

    <section class="filters" aria-label="조회 조건">
      <label>
        <span>기록</span>
        <select v-model="pageKey">
          <option v-for="page in metadata.pages" :key="page.key" :value="page.key">
            {{ pageLabel(page) }}
          </option>
        </select>
      </label>

      <label>
        <span>시즌</span>
        <select v-model="season">
          <option v-for="year in seasons" :key="year" :value="String(year)">
            {{ year }}
          </option>
        </select>
      </label>

      <label>
        <span>시리즈</span>
        <select v-model="seriesCode">
          <option v-for="series in metadata.series" :key="series.code" :value="series.code">
            {{ series.name }}
          </option>
        </select>
      </label>

      <label>
        <span>표시</span>
        <select v-model.number="limit">
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
      </label>

      <button type="button" @click="fetchRecords" :disabled="loading">새로고침</button>
    </section>

    <section class="table-section">
      <div v-if="loading" class="state">불러오는 중</div>
      <div v-else-if="error" class="state error">{{ error }}</div>
      <div v-else-if="!records.length" class="state">표시할 데이터가 없습니다.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th v-for="column in columns" :key="column">{{ column }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id">
              <td v-for="column in columns" :key="`${record.id}-${column}`">
                {{ record.values[column] ?? '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="pager">
      <button type="button" @click="previousPage" :disabled="offset === 0 || loading">이전</button>
      <span>{{ offset + 1 }} - {{ Math.min(offset + limit, total) }} / {{ total }}</span>
      <button type="button" @click="nextPage" :disabled="offset + limit >= total || loading">다음</button>
    </footer>
  </main>
</template>
