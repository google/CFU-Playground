(function(document) {
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var checkbox = document.querySelector('#sidebar-checkbox');
  var top;

  document.addEventListener('click', function(e) {
    var target = e.target;

    if(!checkbox.checked ||
       sidebar.contains(target) ||
       (target === checkbox || target === toggle)){
         if(target === toggle){
           top = document.scrollingElement.scrollTop;
         }
         if(top !== undefined && (target === checkbox || target === toggle)){
           document.scrollingElement.scrollTop = top;
         }
         return;
       }

    checkbox.checked = false;
  }, false);


  var toc = document.querySelector('#toc_container');
  var mastheadPos
  var isAbsolute;
  var tocPos;


  document.addEventListener('scroll', tocFollow);
  window.addEventListener('load', tocFollow);
  window.onresize = function(){
    if (window.innerWidth != screen.width){
      toc.style.display = 'none';
    }
    else{
      toc.style.display = 'inline';
    }
  }

  function tocFollow(tocThresh, mastThresh) {
    tocPos = (toc.getBoundingClientRect().top);
    mastheadPos = (document.querySelector('.masthead').getBoundingClientRect().top);
    isAbsolute = (toc.style.position == 'absolute');
    if (window.location.pathname == '/TinyMLWorkshop/'){
      if(tocPos <= 20 && isAbsolute){
        toc.style.position = 'fixed';
        toc.style.top = '1rem';
      }
      if(mastheadPos > -760 && !isAbsolute){
        toc.style.position = 'absolute';
        toc.style.top = '40rem';
      }
    }
    else{
      if(tocPos <= 20 && isAbsolute){
        toc.style.position = 'fixed';
        toc.style.top = '1rem';
      }
      if(mastheadPos > -75 && !isAbsolute){
        toc.style.position = 'absolute';
        toc.style.top = '5rem';
      }
    }
  }

})(document);
