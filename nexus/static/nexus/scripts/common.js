// Obtenir le chemin du script actuel
var scriptPath = location.href;
var p = scriptPath.lastIndexOf('/');
if (p >= 0) scriptPath = scriptPath.substring(0, p);
scriptPath += '/';

// Obtenir le fichier du script actuel sans paramètres ou fragment
var scriptFile = location.href;
p = scriptFile.indexOf('?'); // Supprime la partie après le "?" (query string)
if (p >= 0) scriptFile = scriptFile.substring(0, p);
p = scriptFile.indexOf('#'); // Supprime la partie après le "#" (fragment)
if (p >= 0) scriptFile = scriptFile.substring(0, p);

// Récupérer la valeur d'un champ à partir de son sélecteur
function getval(name) {
    var obj = document.querySelector(name); // Sélectionne l'élément correspondant
    if (obj == null) return 0;

    var s = parseInt(obj.value, 10); // Convertit la valeur en entier
    return isNaN(s) || s < 0 ? 0 : s; // Retourne 0 si la valeur est invalide
}

// Définir une valeur sur un champ à partir de son sélecteur
function setval(name, val) {
    var obj = document.querySelector(name); // Sélectionne l'élément correspondant
    if (obj) obj.value = val; // Définit la valeur si l'élément existe
}

// Obtenir les dimensions de la fenêtre visible
function getWindowDimensions() {
    // Position de défilement horizontal et vertical
    var scrollX = window.scrollX || document.documentElement.scrollLeft || 0;
    var scrollY = window.scrollY || document.documentElement.scrollTop || 0;

    // Largeur et hauteur de la fenêtre visible
    var width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
    var height = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;

    return { width: scrollX + width, height: scrollY + height };
}

/*
 * Fonction pour formater une chaîne de caractères
 * Remplace les valeurs dans une chaîne basée sur un tableau d'arguments
 * Exemple : format("Hello $name!", { name: "World" }) retourne "Hello World!"
 */
function format(s, args) {
    var rx = new RegExp('\\$([a-z0-9]+)(:[a-z]+|)', 'ig');
    var arr = null;

    while ((arr = rx.exec(s))) {
        var value = args[arr[1]]; // Récupère la valeur associée à la clé

        // Applique des transformations en fonction des modificateurs
        switch (arr[2]) {
            case ':n': // Formate un nombre
                value = formatNumber(value);
                break;
            case ':alliance': // Lien vers une alliance
                value = `<a href="alliance.asp?tag=${value.tag}">[${value.tag}] ${value.name}</a>`;
                break;
            case ':player': // Lien vers un joueur
                value = `<a href="nation.asp?name=${value}">${value}</a>`;
                break;
            case ':research': // Nom d'une recherche
                value = Exile.data.researches[value]?.name || value;
                break;
            default:
                break;
        }

        s = s.replace(arr[0], value); // Remplace la chaîne formatée
    }

    return s;
}

// Ajouter des balises <wbr> pour permettre une coupure dans une chaîne longue
var wbr = "<wbr/>";
if (navigator.userAgent.indexOf("Opera") != -1) wbr = "&#8203;";

function addWbr(str) {
    if (str.length < 30) return str; // Pas besoin de couper si la chaîne est courte

    var s = "";
    for (var k = 0; k < str.length; k += 2) {
        s += str.substr(k, 2) + wbr; // Ajoute <wbr> tous les deux caractères
    }
    return s;
}

// Ajouter des séparateurs de milliers dans un nombre
function addThousands(nStr, outD = '.', sep = ' ') {
    nStr += ''; // Convertit en chaîne de caractères
    var dpos = nStr.indexOf('.'); // Trouve la position du séparateur décimal
    var nStrEnd = '';

    if (dpos != -1) {
        nStrEnd = outD + nStr.substring(dpos + 1); // Garde la partie décimale
        nStr = nStr.substring(0, dpos); // Garde la partie entière
    }

    var rgx = /(\d+)(\d{3})/; // Regex pour insérer les séparateurs
    while (rgx.test(nStr)) {
        nStr = nStr.replace(rgx, '$1' + sep + '$2'); // Ajoute le séparateur
    }
    return nStr + nStrEnd; // Retourne le nombre formaté
}

// Formater un nombre avec séparateurs de milliers
function formatNumber(n) {
    return addThousands(n, '.', ' ');
}

// Ajouter des méthodes au prototype Number
Number.prototype.n = function () {
    return addThousands(this, '.', ' ');
};
Number.prototype.lz = function () {
    return this < 10 ? `0${this}` : `${this}`;
};

// Créer une date UTC à partir d'un timestamp
function UTCDate(x) {
    return new Date(x - new Date().getTimezoneOffset() * 60000);
}
