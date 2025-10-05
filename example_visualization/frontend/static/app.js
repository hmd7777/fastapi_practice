const chartEl = document.getElementById('chart');
const chart = echarts.init(chartEl);

async function loadBarChart() {
  const res = await fetch('http://127.0.0.1:8000/api/bar/avg-sepal-length');
  //const res = await fetch('http://127.0.0.1:8000/api/bar/avg-sepal-length');

  const payload = await res.json(); // { x, y, title, description }

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 40, bottom: 50 },
    xAxis: {
      type: 'category',
      data: payload.x,
      axisLine: { lineStyle: { color: '#888' } },
      axisLabel: { color: '#ccc' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#888' } },
      splitLine: { lineStyle: { color: '#222' } },
      axisLabel: { color: '#ccc' }
    },
    series: [{
      name: 'Count',
      type: 'bar',
      data: payload.y,
      barWidth: '55%',
      itemStyle: { borderRadius: [6,6,0,0] }
    }],
    title: { text: payload.title, left: 'center', textStyle: { color: '#e6e6e6', fontSize: 14 } }
  };

  chart.setOption(option);
  document.getElementById('desc-text').textContent = payload.description;
}

loadBarChart();
window.addEventListener('resize', () => chart.resize());
