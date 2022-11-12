$.getJSON("http://34.149.97.235:80/benchmark/conversion/data", function(obj) {

  const ctx = document.getElementById('myChart').getContext('2d');
  const counts = obj.map(x => x.count)
  const times = obj.map(x => x.min)

  const labels = times

  const myChart = new Chart(ctx, {
      type: 'line',
      data: {
          labels: labels,
          datasets: [{
            label: 'Archivos procesados por minuto',
            data: counts,
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }]
      },
      options: {
          scales: {
              y: {
                  beginAtZero: true
              }
          }
      }
  });

  let sum = myChart.data.datasets[0]
          .data
          .reduce((a, b) => a + b, 0);
  document.getElementById('total').textContent=sum;
});