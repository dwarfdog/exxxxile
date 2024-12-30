document.addEventListener("DOMContentLoaded", function () {
    const passwordForm = document.getElementById("password-form");

    passwordForm.addEventListener("submit", function (event) {
        const newPassword = document.getElementById("new_password").value;
        const newPassword2 = document.getElementById("new_password2").value;

        if (newPassword.length < 6 || newPassword.length > 16) {
            alert("Votre nouveau mot de passe doit être composé d'au moins 6 caractères.");
            event.preventDefault();
            return false;
        }

        if (newPassword !== newPassword2) {
            alert("Les mots de passe ne correspondent pas, veuillez vérifier votre nouveau mot de passe.");
            event.preventDefault();
            return false;
        }
    });
});
