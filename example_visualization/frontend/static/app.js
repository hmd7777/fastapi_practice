const chartEl = document.getElementById('chart');
const chart = echarts.init(chartEl);
const chartSelect = document.getElementById('chart-type');
const chartHeading = document.getElementById('chart-heading');
const chartSubtitle = document.getElementById('chart-subtitle');

const API_BASE = 'http://127.0.0.1:8000/api/';
const chartRegistry = {
  'avg-sepal-length': { endpoint: 'bar/avg-sepal-length', fallbackType: 'bar' },
  'length-difference': { endpoint: 'bar/length-difference', fallbackType: 'bar' },
  'length-width-ratio': { endpoint: 'line/length-width-ratio', fallbackType: 'line' }
};

const palette = ['#d989ff', '#7da5ff', '#b6c4ff', '#94ffc8', '#ffcf7f', '#ff7a7a', '#6d8cff', '#74f1ff'];

function filterLabels(labels = []) {
  const keep = [];
  labels.forEach((label, idx) => {
    if (label && label.toLowerCase() !== 'unknown') {
      keep.push(idx);
    }
  });
  return keep.length ? keep : labels.map((_, idx) => idx);
}

function buildSeries(rawSeries = [], indices, fallbackType, fallbackData = []) {
  const normalised = rawSeries.length ? rawSeries : [
    {
      name: 'Series',
      type: fallbackType,
      data: fallbackData
    }
  ];

  return normalised.map((series, seriesIdx) => {
    const type = series.type || fallbackType;
    const data = (series.data || []).map((point, idx) => ({ value: point, idx }));
    const filteredData = indices.map((keepIdx) => {
      const point = data[keepIdx];
      return point ? point.value : 0;
    });

    if (type === 'bar') {
      return {
        name: series.name,
        type,
        data: filteredData,
        barWidth: '55%',
        itemStyle: {
          color: palette[seriesIdx % palette.length],
          borderRadius: [14, 14, 0, 0]
        }
      };
    }

    return {
      name: series.name,
      type,
      smooth: series.smooth ?? true,
      data: filteredData,
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: palette[seriesIdx % palette.length]
      },
      itemStyle: {
        color: palette[seriesIdx % palette.length]
      }
    };
  });
}

async function loadChart(chartKey = 'avg-sepal-length') {
  const config = chartRegistry[chartKey];
  if (!config) {
    console.warn(`Unknown chart key: ${chartKey}`);
    return;
  }

  const res = await fetch(`${API_BASE}${config.endpoint}`);
  const payload = await res.json();

  const labels = payload.x || [];
  const keep = filterLabels(labels);
  const filteredLabels = keep.map((idx) => labels[idx]);
  const series = buildSeries(payload.series, keep, config.fallbackType, payload.y);

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#d0d4e0', fontFamily: 'Inter, "Segoe UI", sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a1f2d',
      borderColor: '#2a3145',
      textStyle: { color: '#f5f6fb' }
    },
    legend: series.length > 1 ? {
      top: 16,
      right: 10,
      textStyle: { color: '#c0c4d8' },
      icon: 'circle'
    } : undefined,
    grid: { left: 60, right: 30, top: series.length > 1 ? 100 : 70, bottom: 60 },
    xAxis: {
      type: 'category',
      data: filteredLabels,
      axisLine: { lineStyle: { color: '#2d3242' } },
      axisLabel: { color: '#c0c4d8', fontWeight: 500 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2d3242' } },
      splitLine: { lineStyle: { color: '#1d2030' } },
      axisLabel: { color: '#c0c4d8' }
    },
    series,
    title: {
      text: payload.title || '',
      left: 'center',
      textStyle: { color: '#f4f5f7', fontSize: 16, fontWeight: 500 }
    }
  };

  chart.setOption(option, true);
  document.getElementById('desc-text').textContent = payload.description || '';
  chartHeading.textContent = payload.title || 'Iris Chart';
  chartSubtitle.textContent = payload.subtitle || '';
}

chartSelect.addEventListener('change', (event) => {
  loadChart(event.target.value);
});

loadChart(chartSelect.value);
window.addEventListener('resize', () => chart.resize());
