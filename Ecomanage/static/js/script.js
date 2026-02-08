



function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    sidebar.classList.toggle("active");
    overlay.style.display = sidebar.classList.contains("active") ? "block" : "none";

    // Ajouter / supprimer le clic extérieur
    if (sidebar.classList.contains("active")) {
      document.addEventListener("click", handleClickOutside);
    } else {
      document.removeEventListener("click", handleClickOutside);
    }
  }

  function handleClickOutside(event) {
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.querySelector(".toggle-btn");
    const overlay = document.getElementById("overlay");

    if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {
      closeSidebar();
    }
  }

  function closeSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    sidebar.classList.remove("active");
    overlay.style.display = "none";
    document.removeEventListener("click", handleClickOutside);
  }


 

