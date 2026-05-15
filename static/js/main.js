const $ = id => document.getElementById(id);

function fmt(n, decimals = 4) {
  return parseFloat(n).toLocaleString('uk-UA', {
    minimumFractionDigits: 2,
    maximumFractionDigits: decimals
  });
}

async function loadHistory() {
  const res  = await fetch('/history');
  const data = await res.json();
  const list = $('historyList');
  list.innerHTML = '';
  if (!data.length) {
    list.innerHTML = '<div class="empty-history">Ще немає конвертацій</div>';
    return;
  }
  data.forEach(item => {
    const el = document.createElement('div');
    el.className = 'history-item';
    el.innerHTML = `
      <div>
        <div class="hi-main">
          <span class="from">${fmt(item.amount)} ${item.from}</span>
          <span class="arrow">→</span>
          <span class="to">${fmt(item.result)} ${item.to}</span>
        </div>
        <div class="hi-rate">Курс: 1 ${item.from} = ${item.rate} ${item.to}</div>
      </div>
      <div class="hi-date">${item.created}</div>
    `;
    list.appendChild(el);
  });
}

$('convertBtn').addEventListener('click', async () => {
  const btn    = $('convertBtn');
  const errEl  = $('errorMsg');
  const resBox = $('resultBox');

  errEl.className  = 'error-msg';
  resBox.className = 'result-box';

  const amount   = $('amount').value;
  const from_cur = $('from_cur').value;
  const to_cur   = $('to_cur').value;

  if (!amount || +amount <= 0) {
    errEl.textContent = '⚠ Введіть коректну суму';
    errEl.classList.add('show');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Завантаження...';

  try {
    const res  = await fetch('/convert', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ amount, from: from_cur, to: to_cur })
    });
    const data = await res.json();

    if (data.error) {
      errEl.textContent = '⚠ ' + data.error;
      errEl.classList.add('show');
    } else {
      $('resultAmount').textContent = `${fmt(data.result)} ${data.to}`;
      $('resultLabel').textContent  = `${fmt(data.amount)} ${data.from} →`;
      $('resultRate').innerHTML     = `Курс: <b>1 ${data.from} = ${data.rate} ${data.to}</b>`;
      resBox.classList.add('show');
      loadHistory();
    }
  } catch (e) {
    errEl.textContent = '⚠ Помилка мережі';
    errEl.classList.add('show');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Конвертувати';
  }
});

$('swapBtn').addEventListener('click', () => {
  const a = $('from_cur').value;
  const b = $('to_cur').value;
  $('from_cur').value = b;
  $('to_cur').value   = a;
});

$('clearBtn').addEventListener('click', async () => {
  if (!confirm('Очистити всю історію?')) return;
  await fetch('/clear_history', { method: 'POST' });
  loadHistory();
});

$('amount').addEventListener('keydown', e => {
  if (e.key === 'Enter') $('convertBtn').click();
});

loadHistory();
