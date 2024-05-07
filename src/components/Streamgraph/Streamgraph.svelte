<script>
    import { onMount } from 'svelte';
    import * as d3 from 'd3';
    import Navbar from '../Navbar.svelte';
    import { timeFormat } from 'd3-time-format';

    let width = 800; // Define your SVG width
    let height = 600; // Define your SVG height
    let margin = { top: 20, right: 30, bottom: 40, left: 40 }; // Define your margin object

    const timeFormatter = d3.timeFormat('%b');

    async function loadData(){
		  const orders = await d3.csv('data/orders.csv');
      const regions = await d3.csv('data/regions.csv');

		const mergedData = orders.map(order => {
			const region = regions.find(region => region.Territory === order.Territory);
			const deliveryTimeGap = calculateTimeGap(order.OrderDate, order.DeliveryDate);
			return {
                orderId: order.OrderID,
                orderMonth: timeFormatter(new Date(order.OrderDate)),
                deliveryDate: order.DeliveryDate,
                deliveryTimeGap: deliveryTimeGap,
                region: region.Region
            };
		});

        return mergedData.slice(0,10);
	};

    function calculateTimeGap(startDateStr, endDateStr) {

        const startDate = new Date(startDateStr);
        const endDate = new Date(endDateStr);
        const timeDifference = endDate.getTime() - startDate.getTime();
        const timeGapInDays = timeDifference / (1000 * 3600 * 24);

        return timeGapInDays;
	}
    
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    function InitializaStreamGraph(_data)
    {
        const groupedData = d3.group(_data, d => d.region);
        const dataForStack = Array.from(groupedData.entries()).map(([key, values]) => ({
            key,
            data: Array.from(values)
        }));

        const stack = d3.stack()
        .keys(["key"]) // Stack based on the 'value' property    hn
        .order(d3.stackOrderNone) // Maintain the order of input data
        .offset(d3.stackOffsetNone); // Stack directly on top of each other

        const stackedData = stack(dataForStack);

        // const minDate = d3.min(_data, d => d.orderDate);
        // const maxDate = d3.max(_data, d => d.orderDate);
        const minTimeGap = d3.min(_data, d => d.deliveryTimeGap);
        const maxTimeGap = d3.max(_data, d => d.deliveryTimeGap);
        
        // const xScale = d3.scaleBand()
        // .domain(d3.range(12))
        // .range([margin.left, width - margin.right]);

        // const yScale = d3.scaleLinear()
        // .domain([0, d3.max(deliveryTimeGaps)])
        // .rangeRound([height - margin.bottom, margin.top]);
        
        const xScale = d3.scaleTime()
        .domain(d3.range(12))
        .range([margin.left, width - margin.right]);

        const yScale = d3.scaleLinear()
        .domain([minTimeGap, maxTimeGap])
        .rangeRound([height - margin.bottom, margin.top]);
        
        const color = d3.scaleOrdinal()
        .domain(Array.from(groupedData.keys()))
        .range(d3.schemeCategory10);

        const areaGenerator = d3.area()
        .x(d => xScale(d.data.data[0].orderMonth))
        .y0(d => yScale(d[0]))
        .y1(d => yScale(d[1])) 
        .curve(d3.curveCardinal);

        const svg = d3.select('#streamgraph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

        svg.selectAll('path')
        .data(stackedData)
        .join('path')
        .attr('fill', d => color(d.key))
        .attr('d', areaGenerator);

        // Append x-axis
        svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(xScale).tickFormat(i => monthNames[i]));

        // Append y-axis
        svg.append('g')
        .attr('class', 'y-axis')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(yScale));
    }

  // Call the D3 functions on component mount
  onMount(async () => {
    const data = await loadData();
    InitializaStreamGraph(data);
  });
</script>

<Navbar />

<div id="streamgraph">
  <div id="tooltip" style="position: absolute; opacity: 0; pointer-events: none; background: white; border: 1px solid #ccc; padding: 10px;"></div>
</div>

<style>
    #streamgraph svg {
      margin: 0 auto;
      display: block;
      background-color: #f4f4f4;
    }
</style>