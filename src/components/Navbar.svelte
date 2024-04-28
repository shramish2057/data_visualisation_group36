<script>
    import { Link } from 'svelte-routing';
  </script>
  
<nav>
    <ul>
        <li><Link to="/">Home</Link></li>
        <li><Link to="/treemap">Treemap Visualization</Link></li>
    </ul>
</nav>
  
<style>
    nav {
        background: #f4f4f4;
        padding: 1em;
    }
    ul {
        list-style: none;
        padding: 0;
    }
    li {
        display: inline;
        margin-right: 1em;
    }
    a {
        color: #333;
        text-decoration: none;
    }
</style>
  