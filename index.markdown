---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: default
title: Home
---

<!-- <h1> CFU-Playground: Build Your Own Custom TinyML Processor </h1>

A full-stack workshop for accelerating TinyML<br>
*FCCM May 18, 2022*

<div style="display:inline-block;">
  <a style="text-decoration:none" href="https://www.seas.harvard.edu/">
    <img src="{{ '/assets/logos/seas.svg' | relative_url }}" alt="Harvard SEAS" style="height: 2.5rem">
  </a>
</div>
<div style="display:inline-block;">
  <a style="text-decoration:none" href="https://cfu-playground.readthedocs.io/en/latest/">
    <img src="{{ '/assets/logos/google.svg' | relative_url }}" alt="Google" style="height: 2.5rem">
  </a>
</div> -->

<div id="toc_container" style="position: absolute" markdown="1">
<p class="toc_title">Contents</p>

- TOC
{:toc}
</div>

<!-- <div>
{% for event in site.event_pages %}
	<p>{{ event.title }}</p>
{% endfor %}
</div>
 -->

### About 
Running machine learning (ML) on embedded edge devices, as opposed to in the cloud, is gaining increased attention for multiple reasons such as privacy, latency, security, and accessibility. Given the need for energy efficiency when running ML on these embedded platforms, custom processor support and hardware accelerators for such systems could present the needed solutions. However, ML acceleration on microcontroller-class hardware is a new area, and there exists a need for agile hardware customization for tiny machine learning (tinyML). Building ASICs is both costly and time-consuming, though, and the opportunity exists with an FPGA platform to customize the processor to adapt it to perform the application’s computation efficiently while adding a small amount of custom hardware that exploits the bit-level flexibility of FPGAs. 

To this end, we present CFU Playground, a full-stack open-source framework that enables rapid and iterative design of tightly-coupled accelerators for tinyML systems. Our toolchain integrates open-source software, RTL generators, and FPGA tools for synthesis, place, and route. This full-stack development framework gives engineers access to explore bespoke architectures that are customized and co-optimized for tinyML. The rapid deploy-profile-optimization feedback loop lets ML hardware and software developers achieve significant returns out of a relatively small investment in customization for repetitive ML computations. CFU Playground is available as an open-source project here: https://github.com/google/CFU-Playground.

#### What is the goal of the workshop?
- What are some of the challenges and opportunities for designing tinyML hardware?
- How can we design and develop model-specific accelerators quickly on FPGAs?
- Get hands-on knowledge on how to build an ML accelerator using CFU playground!

#### Who is the audience for this workshop?
New ML accelerators are being announced and released each month for a variety of applications. However, the large cost & complexity associated with designing an accelerator, integrating it into a larger System-on-Chip, and developing its software stack has made it a non-trivial task that is difficult for one to rapidly iterate upon. Attendees will be able to deploy their very own accelerated ML solutions within minutes, empowering them to explore the breadth of opportunity that exists in hardware acceleration. This in conjunction with the relevance and excitement surrounding ML today should welcome people with many different backgrounds and interests in ML, FPGAs, embedded systems, computer architecture, hardware design, and software development. 

#### Scope and Topics 
- Custom Hardware Acceleration on FPGAs
- Tiny Machine Learning (TinyML)
- Open-Source Tools/Frameworks for HW & SW Development (Full-Stack)

### Requirements
#### Pre-requisites
- Familiarity with ML “cycle” (inputs, preprocessing, training, inference, etc.)
- Knowledge of computer organization (datapath, registers, opcodes, etc.)
- Basic experience with HDL & synthesis concepts for FPGAs
  - Having used Vivado before & Linux OS is a big plus
  - Must come to the workshop with Vivado already installed
- Need to know C and Python

#### Hardware
- Renode will be used to emulate Arty A7-35T

#### Software
- All software (RISCV toolchain, Symbiflow, etc.) installed in via environment pre-packaged with CFU Playground. 

### Schedule
<div>
<table>
<thead>
  <tr>
    <th>Time</th>
    <th>Material/Activity</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>1:00 PM</td>
    <td>Welcome &amp; Tiny Machine Learning (TinyML)
    	<ul>
    	<li>General overview of tinyML as a field</li>
    	<li>What are the common use cases</li>
    	<li>What kind of models do we run</li>
    	<li>What are the typical resource constraints, challenges, etc.</li>
    	</ul>
    </td>
  </tr>
  <tr>
    <td>1:30 PM</td>
    <td>TensorFlow Lite Microcontrollers (TFLM)
    	<ul>
    		<li>Challenges for running tinyML models</li>
			<li>TF vs. TFLite vs TFLite Micro - deep dive</li>
			<li>Profiling and benchmarking tinyML systems</li>
    	</ul>
	</td>
  </tr>
  <tr>
    <td>2:00 PM</td>
    <td>Benchmarking of TinyML Systems
    	<ul>
    		<li>General overview of CFU</li>
			<li>Make sure Vivado hardware manager can find board</li>
			<li>Install RISC-V toolchain</li>
			<li>Pass golden tests</li>
    	</ul>
	</td>
  </tr>
  <tr>
    <td>2:30 PM</td>
    <td>Custom Function Units
    	<ul>
    		<li>General overview of CFU</li>
			<li>Make sure Vivado hardware manager can find board</li>
			<li>Install RISC-V toolchain</li>
			<li>Pass golden tests</li>
    	</ul>
	</td>
  </tr>
  <tr>
    <td>3:00 PM</td>
    <td>Introduction to Amaranth
		<ul>
			<li>What is Litex</li>
			<li>Explain basic Litex SoC with an example</li>
			<li>Walkthrough simple end-to-end example from README</li>
		</ul>
	</td>
  </tr>
  <tr>
    <td>3:30 PM</td>
    <td>Renode/Antmicro
    	<ul>
			<li>TBD</li>
    	</ul>
    </td>
  </tr>
  <tr>
    <td>4:00 PM</td>
    <td>Accelerate your own TinyML Model
    	<ul>
			<li>Pick a task and train a model using TFLM</li>
			<li>Get it running on the board</li>
			<li>Build your own CFU</li>
			<li>Measure performance speed up</li>
    	</ul>
    </td>
  </tr>
</tbody>
</table>
</div>
