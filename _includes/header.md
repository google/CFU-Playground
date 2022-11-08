<style>
	.header-container {
		color: #fff;
		font-size: 22px;
	}
	.header-container > h1 {
		font-size: 52px;
		color: #fff;
	}
</style>

<div class="header-container">
{% if page.hpca %}
<h1><b> TinyML: Accelerating Tiny Machine Learning by Building Your Own Processor (BYOP) </b></h1><br><br>
{% elsif page.conference %}
<h1><b> Build Your Own Custom TinyML Processor </b></h1><br><br>
{% else %}
<h1><b> CFU-Playground</b></h1><br><br>
{% endif %}

<p>
{% if page.conference %}
A full-stack workshop for accelerating TinyML<br>
{{page.conference}} | {{page.prettify-conference-date}}<br>
{% else %}
A full-stack open-source framework for accelerating TinyML<br>
{% endif %}
</p>

<div style="display:inline-block;">
  <a style="text-decoration:none" href="https://cfu-playground.readthedocs.io/en/latest/">
    <img src="{{ '/assets/logos/google.svg' | relative_url }}" alt="Google" style="height: 2.5rem">
  </a>
</div>
<div style="display:inline-block;">
  <a style="text-decoration:none" href="https://edge.seas.harvard.edu/">
    <img src="{{ '/assets/logos/seas.svg' | relative_url }}" alt="Harvard SEAS" style="height: 2.5rem">
  </a>
</div>
<!--<div style="display:inline-block;">
  <a style="text-decoration:none" href="https://www.antmicro.com">
    <img src="{{ '/assets/logos/AntMicro.svg' | relative_url }}" alt="AntMicro" style="height: 2.5rem">
  </a>
</div>
-->
</div>
