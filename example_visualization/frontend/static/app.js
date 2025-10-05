const chartEl = document.getElementById('chart');
const chart = echarts.init(chartEl);

async function loadBarChart() {
  const res = await fetch('http://127.0.0.1:8000/api/bar/avg-sepal-length');
  //const res = await fetch('http://127.0.0.1:8000/api/bar/avg-sepal-length');

  const payload = await res.json(); // { x, y, title, description }

  const filtered = payload.x.reduce((acc, label, idx) => {
    if (label.toLowerCase() === 'unknown') {
      return acc;
    }
    acc.labels.push(label);
    acc.values.push(payload.y[idx]);
    return acc;
  }, { labels: [], values: [] });

  const palette = ['#d989ff', '#7da5ff', '#b6c4ff', '#94ffc8', '#ffcf7f', '#ff7a7a', '#6d8cff', '#74f1ff'];

  const labels = filtered.labels.length ? filtered.labels : payload.x;
  const values = filtered.values.length ? filtered.values : payload.y;

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#d0d4e0', fontFamily: 'Inter, "Segoe UI", sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a1f2d',
      borderColor: '#2a3145',
      textStyle: { color: '#f5f6fb' }
    },
    grid: { left: 60, right: 30, top: 60, bottom: 60 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#2d3242' } },
      axisLabel: { color: '#c0c4d8', fontWeight: 500 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2d3242' } },
      splitLine: { lineStyle: { color: '#1d2030' } },
      axisLabel: { color: '#c0c4d8' }
    },
    series: [{
      name: 'Count',
      type: 'bar',
      data: values.map((value, idx) => ({
        value,
        itemStyle: {
          color: palette[idx % palette.length],
          borderRadius: [14, 14, 0, 0]
        }
      })),
      barWidth: '55%'
    }],
    title: {
      text: payload.title,
      left: 'center',
      textStyle: { color: '#f4f5f7', fontSize: 16, fontWeight: 500 }
    }
  };

  chart.setOption(option);
  document.getElementById('desc-text').textContent = payload.description;
}

loadBarChart();
window.addEventListener('resize', () => chart.resize());
