document.addEventListener('DOMContentLoaded', () => {
  // 学者データの読み込み
  let scholars = [];
  let drawnScholars = [];
  let activeFilter = 'all';
  
  async function loadScholars() {
    try {
      const response = await fetch('scholars_enhanced_tavily.json');
      scholars = await response.json();
      console.log(`${scholars.length}人の学者データを読み込みました`);
    } catch (error) {
      console.error('学者データの読み込みに失敗しました:', error);
    }
  }
  
  // ガチャ処理
  function drawScholar() {
    if (scholars.length === 0) return null;
    
    // フィルター適用
    let availableScholars = scholars;
    if (activeFilter !== 'all') {
      availableScholars = scholars.filter(s => 
        s.tags.some(tag => tag === activeFilter)
      );
      
      if (availableScholars.length === 0) {
        alert(`${activeFilter}のカテゴリに該当する学者がいません。`);
        return null;
      }
    }
    
    // 既に引いた学者を除外
    availableScholars = availableScholars.filter(s => !drawnScholars.includes(s.id));
    
    // すべての学者を引いた場合はリセット
    if (availableScholars.length === 0) {
      drawnScholars = [];
      return drawScholar();
    }
    
    const scholar = availableScholars[Math.floor(Math.random() * availableScholars.length)];
    drawnScholars.push(scholar.id);
    return scholar;
  }
  
  // カード表示
  function renderCard(scholar) {
    const cardElement = document.createElement('div');
    cardElement.className = `card card-anim rarity-frame-${scholar.rarity}`;
    
    const rarityClass = `rarity-${scholar.rarity}`;
    
    // 画像パスの調整（nullの場合はプレースホルダー）
    const avatarPath = scholar.avatar || 'https://via.placeholder.com/300x300?text=No+Image';
    
    // レア度に応じた背景エフェクトを追加
    let backgroundEffect = '';
    if (scholar.rarity === 'SSR' || scholar.rarity === 'SR') {
      backgroundEffect = `<div class="card-background-effect background-${scholar.rarity}"></div>`;
    }
    
    cardElement.innerHTML = `
      ${backgroundEffect}
      <img class="card-img" src="${avatarPath}" alt="${scholar.name.ja}">
      <div class="card-rarity ${rarityClass}">${scholar.rarity}</div>
      <div class="card-content">
        <h3>${scholar.name.ja}</h3>
        <div>${scholar.name.en}</div>
        <div class="card-affiliation">${scholar.affiliation}</div>
        
        <!-- タグを非表示に変更 -->
        
        <!-- 貢献セクション -->
        <div class="contribution-section">
          <h4>貢献</h4>
          <div class="contribution-text">${scholar.contribution.text}</div>
          <!-- 出典の詳細リンクを非表示に変更 -->
        </div>
        
        <!-- 豆知識セクション -->
        <div class="trivia-section">
          <h4>豆知識</h4>
          <div class="trivia-text">${scholar.trivia}</div>
          <!-- 出典の詳細リンクを非表示に変更 -->
        </div>
      </div>
    `;
    
    return cardElement;
  }
  
  // ガチャ演出（カードが順番にスライドイン）
  function gachaAnimation(cardElement, delay = 0) {
    cardElement.style.opacity = '0';
    cardElement.style.transform = 'translateY(50px)';
    
    setTimeout(() => {
      cardElement.style.opacity = '1';
      cardElement.style.transform = 'translateY(0)';
    }, delay);
  }
  
  // ガチャボタン処理
  document.getElementById('pull-one').addEventListener('click', () => {
    const resultArea = document.getElementById('gacha-result');
    resultArea.innerHTML = '';
    
    const scholar = drawScholar();
    if (scholar) {
      const cardElement = renderCard(scholar);
      resultArea.appendChild(cardElement);
      gachaAnimation(cardElement);
      
      // レア度に応じたエフェクト
      if (scholar.rarity === 'SSR') {
        playSSREffect();
      } else if (scholar.rarity === 'SR') {
        playSREffect();
      }
    }
  });
  
  // SSR演出
  function playSSREffect() {
    const body = document.querySelector('body');
    
    // フラッシュエフェクト
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.background = 'radial-gradient(circle, rgba(255,215,0,0.8) 0%, rgba(255,255,255,0) 70%)';
    overlay.style.pointerEvents = 'none';
    overlay.style.zIndex = '999';
    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.3s ease';
    
    body.appendChild(overlay);
    
    // キラキラエフェクト（パーティクル）
    const particles = document.createElement('div');
    particles.style.position = 'fixed';
    particles.style.top = '0';
    particles.style.left = '0';
    particles.style.width = '100%';
    particles.style.height = '100%';
    particles.style.pointerEvents = 'none';
    particles.style.zIndex = '998';
    body.appendChild(particles);
    
    // 20個のパーティクルを生成
    for (let i = 0; i < 20; i++) {
      createParticle(particles);
    }
    
    // SSRテキスト演出
    const ssrText = document.createElement('div');
    ssrText.textContent = 'SSR GET!!';
    ssrText.style.position = 'fixed';
    ssrText.style.top = '50%';
    ssrText.style.left = '50%';
    ssrText.style.transform = 'translate(-50%, -50%) scale(0)';
    ssrText.style.fontSize = '5rem';
    ssrText.style.fontWeight = 'bold';
    ssrText.style.color = 'gold';
    ssrText.style.textShadow = '0 0 10px rgba(255,215,0,0.8), 0 0 20px rgba(255,215,0,0.5)';
    ssrText.style.zIndex = '1000';
    ssrText.style.transition = 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    body.appendChild(ssrText);
    
    // アニメーション実行
    setTimeout(() => {
      overlay.style.opacity = '1';
      ssrText.style.transform = 'translate(-50%, -50%) scale(1)';
      
      setTimeout(() => {
        overlay.style.opacity = '0';
        ssrText.style.transform = 'translate(-50%, -50%) scale(0)';
        
        setTimeout(() => {
          body.removeChild(overlay);
          body.removeChild(ssrText);
          body.removeChild(particles);
        }, 500);
      }, 1000);
    }, 10);
  }
  
  // キラキラパーティクル生成
  function createParticle(container) {
    const particle = document.createElement('div');
    const size = Math.random() * 15 + 5;
    
    particle.style.position = 'absolute';
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.background = 'gold';
    particle.style.borderRadius = '50%';
    particle.style.boxShadow = '0 0 10px rgba(255,215,0,0.8)';
    
    // ランダムな位置と動き
    const startX = Math.random() * window.innerWidth;
    const startY = Math.random() * window.innerHeight;
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 100 + 50;
    
    particle.style.left = `${startX}px`;
    particle.style.top = `${startY}px`;
    
    container.appendChild(particle);
    
    // パーティクルのアニメーション
    const startTime = Date.now();
    const duration = Math.random() * 1000 + 1000;
    
    function animate() {
      const elapsed = Date.now() - startTime;
      const progress = elapsed / duration;
      
      if (progress >= 1) {
        container.removeChild(particle);
        return;
      }
      
      const x = startX + Math.cos(angle) * speed * progress;
      const y = startY + Math.sin(angle) * speed * progress;
      const scale = 1 - progress;
      
      particle.style.left = `${x}px`;
      particle.style.top = `${y}px`;
      particle.style.opacity = scale.toString();
      particle.style.transform = `scale(${scale})`;
      
      requestAnimationFrame(animate);
    }
    
    requestAnimationFrame(animate);
  }
  
  // SR演出
  function playSREffect() {
    const body = document.querySelector('body');
    
    // フラッシュエフェクト
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.background = 'radial-gradient(circle, rgba(192,192,192,0.6) 0%, rgba(255,255,255,0) 70%)';
    overlay.style.pointerEvents = 'none';
    overlay.style.zIndex = '999';
    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.3s ease';
    
    body.appendChild(overlay);
    
    // SRテキスト演出
    const srText = document.createElement('div');
    srText.textContent = 'SR!';
    srText.style.position = 'fixed';
    srText.style.top = '50%';
    srText.style.left = '50%';
    srText.style.transform = 'translate(-50%, -50%) scale(0)';
    srText.style.fontSize = '4rem';
    srText.style.fontWeight = 'bold';
    srText.style.color = 'silver';
    srText.style.textShadow = '0 0 8px rgba(192,192,192,0.6)';
    srText.style.zIndex = '1000';
    srText.style.transition = 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    body.appendChild(srText);
    
    // アニメーション実行
    setTimeout(() => {
      overlay.style.opacity = '1';
      srText.style.transform = 'translate(-50%, -50%) scale(1)';
      
      setTimeout(() => {
        overlay.style.opacity = '0';
        srText.style.transform = 'translate(-50%, -50%) scale(0)';
        
        setTimeout(() => {
          body.removeChild(overlay);
          body.removeChild(srText);
        }, 300);
      }, 800);
    }, 10);
  }
  
  // 初期化
  loadScholars();
});
