<script>
  import { onMount } from 'svelte';
  import Papa from 'papaparse';

  let ordersData = [];
  let productsData = [];
  let mergedData = [];

  async function loadData() {
    // Load orders data
    const ordersResponse = await fetch('orders.csv');
    const ordersText = await ordersResponse.text();
    ordersData = Papa.parse(ordersText, { header: true }).data;

    // Load products data
    const productsResponse = await fetch('products.csv');
    const productsText = await productsResponse.text();
    productsData = Papa.parse(productsText, { header: true }).data;

    // Explode and merge data
    explodeAndMergeData();
  }

  function explodeAndMergeData() {
    mergedData = [];

    ordersData.forEach(order => {
      const productIds = order.ProductIDs.split(';').map(id => id.trim());
      const quantities = order.Quantities.split(';').map(qty => qty.trim());

      productIds.forEach((productId, index) => {
        const product = productsData.find(product => product.product_code === productId);
        if (product) {
          mergedData.push({
            ProductIDs: productId,
            Quantities: quantities[index],
            Type: product.Type,
            Subtype: product.Subtype
          });
        }
      });
    });
  }

  onMount(loadData);
</script>

<h1>Loading data...</h1>

{#if mergedData.length > 0}
  <table>
    <thead>
      <tr>
        <th>ProductIDs</th>
        <th>Quantities</th>
        <th>Type</th>
        <th>Subtype</th>
      </tr>
    </thead>
    <tbody>
      {#each mergedData as item}
        <tr>
          <td>{item.ProductIDs}</td>
          <td>{item.Quantities}</td>
          <td>{item.Type}</td>
          <td>{item.Subtype}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{:else}
  <p>No data loaded.</p>
{/if}

<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let treeData = {};

  async function loadData() {
    // Load data and organize it into a hierarchical structure
    // For simplicity, let's assume the data is already in the correct format
    treeData = {
      name: 'Products',
      children: [
        {
          name: 'ADVENTURING EQUIPMENT',
          children: [
            { name: 'CONTAINER' },
            { name: 'IOUN STONE' },
            { name: 'MAGIC UTILITY' },
            { name: 'WAND' },
            { name: 'HELMET' },
            { name: 'CLOTHING' },
            { name: 'SPELL FOCUS' },
            { name: 'SURVIVAL & WILDERNESS' },
            { name: 'TOOLS' },
            { name: 'BELT / GIRDLE' },
            { name: 'ROD' },
            { name: 'GAUNTLETS / GLOVES' },
            { name: 'GOGGLES' },
            { name: 'CLOAK' },
            { name: 'BOOTS' },
            { name: 'WIND INSTRUMENT' },
            { name: 'BRACERS' },
            { name: 'SIMPLE MELEE WEAPON' },
            { name: 'GAMING SET' }
          ]
        },
        {
          name: 'ANIMALS & TRANSPORTATION',
          children: [
            { name: 'MOUNT' },
            { name: 'LIVESTOCK' },
            { name: 'VEHICLE' }
          ]
        },
        {
          name: 'ARMS & ARMOUR',
          children: [
            { name: 'LIGHT ARMOUR' },
            { name: 'SIMPLE MELEE WEAPON' },
            { name: 'MARTIAL MELEE WEAPON' },
            { name: 'MARTIAL RANGED WEAPON' },
            { name: 'MEDIUM ARMOUR' },
            { name: 'HEAVY ARMOUR' },
            { name: 'WAND' },
            { name: 'STAFF' },
            { name: 'BRACERS' },
            { name: 'ARMOUR OTHER' },
            { name: 'AMMUNITION' },
            { name: 'HELMET' },
            { name: 'SHIELD' },
            { name: 'CLOAK' },
            { name: 'SIMPLE RANGED WEAPON' },
            { name: 'ROD' },
            { name: 'WEAPON OTHER' },
            { name: 'BOOTS' },
            { name: 'GOGGLES' },
            { name: 'GAUNTLETS / GLOVES' }
          ]
        },
        {
          name: 'JEWELRY',
          children: [
            { name: 'RING' },
            { name: 'AMULET / NECKLACE' },
            { name: 'MAGIC UTILITY' }
          ]
        },
        {
          name: 'MUSICAL INSTRUMENT',
          children: [
            { name: 'STRING INSTRUMENT' },
            { name: 'WIND INSTRUMENT' },
            { name: 'BRASS INSTRUMENT' },
            { name: 'PERCUSSION INSTRUMENT' }
          ]
        },
        {
          name: 'POTIONS & SCROLLS',
          children: [
            { name: 'SCROLL' },
            { name: 'POTIONS & ALCHEMY' }
          ]
        },
        {
          name: 'SUMMONING DEVICE',
          children: [
            { name: 'SUMMONING DEVICE' },
            { name: 'RING' }
          ]
        },
        {
          name: 'TOOLS & KITS',
          children: [
            { name: 'TOOLS' },
            { name: 'CONTAINER' },
            { name: 'TOOL KITS' },
            { name: 'GAMING SET' },
            { name: 'SURVIVAL & WILDERNESS' }
          ]
        }
      ]
    };

    // Calculate values for each node based on orders data
    calculateValues(treeData);

    // Render the tree visualization
    renderTree();
  }

  function calculateValues(node) {
    // Initialize values
    node.ordersCount = 0;
    node.quantitiesSum = 0;

    // Recursively calculate values for children
    if (node.children) {
      node.children.forEach(child => {
        calculateValues(child);
        node.ordersCount += child.ordersCount || 0;
        node.quantitiesSum += child.quantitiesSum || 0;
      });
    }

    // Calculate values based on orders data (assuming mergedData is available)
    if (node.name !== 'Products') {
      node.ordersCount = mergedData.filter(item => item.Type === node.name).length;
      node.quantitiesSum = mergedData.filter(item => item.Type === node.name).reduce((sum, item) => sum + parseInt(item.Quantities), 0);
    }
  }

  function renderTree() {
    const width = 600;
    const height = 400;

    const svg = d3.select('#tree-container')
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', 'translate(50,50)');

    const treeLayout = d3.tree().size([width - 100, height - 100]);

    const root = d3.hierarchy(treeData);

    treeLayout(root);

    const links = svg.selectAll('.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x)
      );

    const nodes = svg.selectAll('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.y},${d.x})`)
      .on('click', toggleSubtypes)
      .on('mouseover', showTooltip)
      .on('mouseout', hideTooltip);

    nodes.append('circle')
      .attr('r', 5);

    nodes.append('text')
      .attr('dy', 3)
      .attr('x', d => d.children ? -8 : 8)
      .style('text-anchor', d => d.children ? 'end' : 'start')
      .text(d => d.data.name);

    function toggleSubtypes(event, d) {
      if (d.children) {
        d.children = null;
      } else {
        d.children = d.data._children;
      }
      treeLayout(root);
      update(svg, root);
    }

    function showTooltip(event, d) {
      // Display tooltip with quantities sold and number of orders
      const tooltip = d3.select('#tooltip');
      tooltip.style('display', 'block')
        .style('left', `${event.pageX}px`)
        .style('top', `${event.pageY}px`)
        .html(`
          <div>Type/Subtype: ${d.data.name}</div>
          <div>Orders Count: ${d.data.ordersCount}</div>
          <div>Quantities Sum: ${d.data.quantitiesSum}</div>
        `);
    }

    function hideTooltip() {
      // Hide tooltip
      const tooltip = d3.select('#tooltip');
      tooltip.style('display', 'none');
    }

    function update(svg, source) {
      const nodes = root.descendants().filter(d => d.parent !== null);

      const node = svg.selectAll('.node')
        .data(nodes, d => d.data.name);

      node.exit().remove();

      const newNode = node.enter().append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${source.y},${source.x})`)
        .on('click', toggleSubtypes)
        .on('mouseover', showTooltip)
        .on('mouseout', hideTooltip);

      newNode.append('circle')
        .attr('r', 5)
        .style('fill', d => d.children ? 'lightsteelblue' : '#fff');

      newNode.append('text')
        .attr('dy', 3)
        .attr('x', d => d.children ? -8 : 8)
        .style('text-anchor', d => d.children ? 'end' : 'start')
        .text(d => d.data.name);

      const link = svg.selectAll('.link')
        .data(root.links(), d => d.target.data.name);

      link.exit().remove();

      const newLink = link.enter().append('path')
        .attr('class', 'link')
        .attr('d', d3.linkHorizontal()
          .x(d => source.y)
          .y(d => source.x)
        );

      link.merge(newLink)
        .transition()
        .duration(500)
        .attr('d', d3.linkHorizontal()
          .x(d => d.y)
          .y(d => d.x)
        );
    }
  }

  onMount(loadData);
</script>

<div id="tree-container"></div>

<div id="tooltip" style="position: absolute; display: none; background-color: rgba(255, 255, 255, 0.9); padding: 5px; border: 
