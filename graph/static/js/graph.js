// static/js/graph.js

// 全局变量
let selectedNode = null;
let graphData = null;

// 当页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 从后端获取数据
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            graphData = data;
            renderGraph(data);
            updateCategoriesLegend(data.categories);
            updateCounters(data.nodes.length, data.links.length);
        })
        .catch(error => console.error('获取数据错误:', error));
});

// 渲染知识图谱
function renderGraph(data) {
    const width = document.querySelector('.graph-container').clientWidth;
    const height = document.querySelector('.graph-container').clientHeight;
    
    // 创建SVG
    const svg = d3.select('#graph-svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);
    
    // 添加缩放行为
    const zoomBehavior = d3.zoom()
        .scaleExtent([0.1, 3])
        .on('zoom', (event) => {
            container.attr('transform', event.transform);
            updateZoomLevel(Math.round(event.transform.k * 100));
        });
    
    svg.call(zoomBehavior);
    
    // 创建容器
    const container = svg.append('g')
        .attr('class', 'container');
    
    // 创建力导向模拟
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide().radius(d => getNodeRadius(d) + 2));
    
    // 基于流行度确定节点半径
    function getNodeRadius(node) {
        return 10 + (node.popularity * 0.15);
    }
    
    // 根据分类获取节点颜色
    function getNodeColor(node) {
        const category = data.categories.find(c => c.name === node.category);
        return category ? category.color : '#999';
    }
    
    // 绘制连接线
    const link = container.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(data.links)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.max(1, d.strength * 3));
    
    // 创建节点组
    const node = container.append('g')
        .attr('class', 'nodes')
        .selectAll('.node')
        .data(data.nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // 添加圆形背景
    node.append('circle')
        .attr('r', getNodeRadius)
        .attr('fill', getNodeColor)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
    
    // 添加悬停效果
    node.append('circle')
        .attr('class', 'hover-effect')
        .attr('r', d => getNodeRadius(d) + 8)
        .attr('fill', 'rgba(150, 150, 150, 0.2)')
        .attr('stroke', '#666')
        .attr('stroke-width', 0.5)
        .style('opacity', 0);
    
    // 添加标签
    node.append('text')
        .text(d => d.name)
        .attr('font-size', d => 10 + (d.popularity * 0.03))
        .attr('dx', d => getNodeRadius(d) + 5)
        .attr('dy', 4)
        .attr('fill', '#333');
    
    // 节点交互
    node.on('mouseover', (event, d) => {
        showHoverInfo(d);
        d3.select(event.currentTarget).select('.hover-effect').style('opacity', 1);
        
        // 高亮连接
        link.attr('stroke', l => (l.source.id === d.id || l.target.id === d.id) ? '#000' : '#999')
            .attr('stroke-opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.2)
            .attr('stroke-width', l => (l.source.id === d.id || l.target.id === d.id) ? Math.max(2, l.strength * 4) : Math.max(1, l.strength * 3));
        
        // 高亮连接的节点
        node.select('circle').attr('stroke-width', n => 
            data.links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.source.id === n.id && l.target.id === d.id)) ? 3 : 1.5
        );
    })
    .on('mouseout', (event, d) => {
        hideHoverInfo();
        d3.select(event.currentTarget).select('.hover-effect').style('opacity', 0);
        
        // 如果没有选中节点，则重置高亮
        if (!selectedNode) {
            link.attr('stroke', '#999')
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', d => Math.max(1, d.strength * 3));
            
            node.select('circle').attr('stroke-width', 1.5);
        }
    })
    .on('click', (event, d) => {
        selectedNode = d;
        showPoiDetails(d, data);
        
        // 根据选择更新视觉状态
        node.select('circle').attr('stroke-width', n => n.id === d.id ? 3 : 1.5);
    });
    
    // 更新位置
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x}, ${d.y})`);
    });
    
    // 拖动函数
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // 点击其他区域取消选择
    svg.on('click', function(event) {
        if (event.target === this) {
            selectedNode = null;
            hidePoiDetails();
            
            // 重置高亮
            link.attr('stroke', '#999')
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', d => Math.max(1, d.strength * 3));
            
            node.select('circle').attr('stroke-width', 1.5);
        }
    });
}

// 显示POI悬停信息
function showHoverInfo(poi) {
    document.getElementById('default-message').style.display = 'none';
    document.getElementById('poi-details').style.display = 'none';
    
    const hoverInfo = document.getElementById('hover-info');
    document.getElementById('hover-name').textContent = poi.name;
    hoverInfo.style.display = 'block';
}

// 隐藏悬停信息
function hideHoverInfo() {
    const hoverInfo = document.getElementById('hover-info');
    hoverInfo.style.display = 'none';
    
    if (document.getElementById('poi-details').style.display === 'none') {
        document.getElementById('default-message').style.display = 'block';
    }
}

// 显示POI详细信息
function showPoiDetails(poi, data) {
    document.getElementById('default-message').style.display = 'none';
    document.getElementById('hover-info').style.display = 'none';
    
    const poiDetails = document.getElementById('poi-details');
    poiDetails.style.display = 'block';
    
    // 获取分类信息
    const category = data.categories.find(c => c.name === poi.category);
    
    // 生成评分星星
    let starsHtml = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.floor(poi.rating)) {
            starsHtml += '<span>★</span>';
        } else if (i - 0.5 <= poi.rating) {
            starsHtml += '<span>★</span>';
        } else {
            starsHtml += '<span class="empty-star">★</span>';
        }
    }
    
    // 获取连接的POI
    const connectedPois = data.links
        .filter(link => link.source.id === poi.id || link.target.id === poi.id)
        .map(link => link.source.id === poi.id ? link.target : link.source);
    
    // 创建连接POI列表
    let connectedPoisHtml = '';
    connectedPois.forEach(connectedPoi => {
        const connectedCategory = data.categories.find(c => c.name === connectedPoi.category);
        connectedPoisHtml += `
            <div class="connected-poi" onclick="selectPoi(${connectedPoi.id})">
                • ${connectedPoi.name} 
                <small style="color: ${connectedCategory.color};">(${connectedPoi.category})</small>
            </div>
        `;
    });
    
    // 生成HTML
    poiDetails.innerHTML = `
        <div class="poi-detail">
            <div class="poi-name">${poi.name}</div>
            
            <div class="category-badge" style="background-color: ${category.color}">
                ${poi.category}
            </div>
            
            <div class="d-flex align-items-center mb-3">
                <div class="rating-stars me-2">
                    ${starsHtml}
                </div>
                <span class="small">${poi.rating} (${poi.reviews} 条评价)</span>
            </div>
            
            <div class="poi-image">
                <img src="/static/images/placeholder.jpg" alt="${poi.name}" class="img-fluid">
            </div>
            
            <p class="mb-4">${poi.description}</p>
            
            <div class="info-row">
                <div class="info-label">地址：</div>
                <div class="info-value">${poi.address}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">开放时间：</div>
                <div class="info-value">${poi.opening_hours}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">门票：</div>
                <div class="info-value">${poi.ticket_price}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">最佳季节：</div>
                <div class="info-value">${poi.best_season}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">交通：</div>
                <div class="info-value">${poi.transportation}</div>
            </div>
            
            <div class="info-row">
                <div class="info-label">小贴士：</div>
                <div class="info-value">${poi.tips}</div>
            </div>
            
            <div class="mt-4">
                <div class="section-title">历史意义：</div>
                <p class="small text-muted">${poi.historical_significance}</p>
            </div>
            
            <div class="mt-4">
                <div class="section-title">收录年份：</div>
                <p class="small">${poi.year}</p>
            </div>
        </div>
        
        <div class="mt-4">
            <div class="section-title">连接的景点：</div>
            <div class="connected-pois">
                ${connectedPoisHtml || '<div class="text-muted small">无连接景点</div>'}
            </div>
        </div>
        
        <div class="mt-4 mb-4">
            <div class="section-title">用户评价：</div>
            <div class="reviews">
                <div class="review">
                    <div class="review-title">美丽的地方！</div>
                    <p class="review-content">这个地方太棒了，喜欢这里的氛围和风景。到杭州一定要来。</p>
                </div>
                <div class="review">
                    <div class="review-title">很值得一游</div>
                    <p class="review-content">景点维护得很好，有很重要的历史意义。强烈推荐！</p>
                </div>
            </div>
        </div>
    `;
}

// 通过ID选择POI
function selectPoi(poiId) {
    const poi = graphData.nodes.find(node => node.id === poiId);
    if (poi) {
        selectedNode = poi;
        showPoiDetails(poi, graphData);
    }
}

// 隐藏POI详细信息
function hidePoiDetails() {
    document.getElementById('poi-details').style.display = 'none';
    document.getElementById('default-message').style.display = 'block';
}

// 更新分类图例
function updateCategoriesLegend(categories) {
    const legend = document.getElementById('categories-legend');
    legend.innerHTML = ''; // 清空现有内容
    
    categories.forEach(category => {
        const item = document.createElement('div');
        item.className = 'category-indicator';
        item.innerHTML = `
            <div class="category-color" style="background-color: ${category.color}"></div>
            <span class="small">${category.name}</span>
        `;
        legend.appendChild(item);
    });
}

// 更新计数器
function updateCounters(nodeCount, linkCount) {
    document.getElementById('node-count').textContent = nodeCount;
    document.getElementById('link-count').textContent = linkCount;
}

// 更新缩放级别
function updateZoomLevel(level) {
    document.getElementById('zoom-level').textContent = level + '%';
}