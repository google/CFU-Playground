---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home-page
title: Home
---

# Welcome
<iframe src="https://drive.google.com/file/d/1l1eUSqSeUHHzTSWsa8wW87NKzPhfnYuy/preview" width="746" height="449" allow="autoplay"></iframe>


# Github
<h3>
  <a href="https://github.com/google/CFU-Playground">
      CFU-Playground Repository
  </a>
</h3>


# Documentation
<h3>
  <a href="https://cfu-playground.readthedocs.io/en/latest/">
      CFU-Playground ReadTheDocs
  </a>
</h3>


# Accepted Workshop Venues
{% assign workshops = site.workshops | sort: 'date' %}
{% for workshop in workshops reversed %}
  <h3>
    {% if workshop.canceled %}
    <a href="{{ workshop.conference-url }} ">
      {{workshop.conference}} | {{workshop.prettify-conference-date}} 
    </a>
    {% else %}
    <a href="{{ workshop.url | prepend: site.baseurl }} ">
      {{workshop.conference}} | {{workshop.prettify-conference-date}} 
    </a>
    {% endif %}
  </h3>
{% endfor %}

# Publications, Posters and Presentations
<h3>
  <a href="https://arxiv.org/abs/2201.01863">
      Paper
  </a>
</h3>
<h3>
  <a href="https://cms.tinyml.org/wp-content/uploads/talks2022/Shvetank-Prakash-SW-tools.pdf">
      TinyML Summit Poster | 2022
  </a>
</h3>
<h3>
  <a href="https://59dac.conference-program.com/presentation/?id=WIP198&sess=sess263">
      DAC Poster | 2022
  </a>
</h3>


<!-- Line Break to leave space at bottom of page for aesthetic-->
<br>
