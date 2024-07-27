import { TrackballControls } from 'three/addons/controls/TrackballControls.js';

const countryColors = {
    "USA": 0xffffff,
    "Russia": 0xffd166,
    "China": 0x2ca02c,
    "India": 0xd62728,
    "Japan": 0x9467bd,
    "Unknown": 0x80ed99
    // Add more countries and colors as needed
};
const EARTH_RADIUS_KM = 6371; // km
const SAT_SIZE = 80; // km
let TIME_STEP = 1 * 1000; // per frame
let satellitesMoving = true;

const timeLogger = document.getElementById('time-log');
const tooltip = document.getElementById('tooltip');
const satelliteInfo = document.getElementById('satellite-info');

const Globe = new ThreeGlobe()
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
    .objectLat('lat')
    .objectLng('lng')
    .objectAltitude('alt')
    .objectFacesSurface(false);

const satGeometry = new THREE.OctahedronGeometry(SAT_SIZE * Globe.getGlobeRadius() / EARTH_RADIUS_KM / 2, 0);

Globe.objectThreeObject((d) => {
    const color = countryColors[d.country] || 0xffffff;
    const satMaterial = new THREE.MeshLambertMaterial({ color: color, transparent: true, opacity: 1 });
    const satMesh = new THREE.Mesh(satGeometry, satMaterial);
    satMesh.userData = { satData: d }; // Assign satellite data to userData
    return satMesh;
});

let satData = [];
let globalpath = ''
let intervalId = null;

function loadSatellites(path) {
    if (intervalId) {
        clearInterval(intervalId);
        if (satellitesMoving) {
            setInterval(update, TIME_STEP)
        }
    }
    console.log(intervalId, 'hello world')

    if (globalpath === path) {
        return;
    } else {
        globalpath = path;
    }
    axios.get(path)
        .then(response => {
            const rawData = response.data;
            const tleData = rawData.replace(/\r/g, '').split(/\n(?=[^12])/).map(tle => tle.split('\n'));
            // console.log(tleData)
            satData = tleData.map(([name, ...tle]) => {
                let country

                if (name.includes('STARLINK'))
                    country = 'USA'
                else if (name.includes('COSMOS'))
                    country = 'Russia'
                else
                    country = 'Unknown'
                return ({
                    satrec: satellite.twoline2satrec(...tle),
                    name: name.trim().replace(/^0 /, ''),
                    country
                })
            }
            );
            intervalId = setInterval(update, TIME_STEP);
            updateSatellites();
        })
        .catch(error => console.error('Error loading satellite data:', error));
}

function update() {
    let time = new Date();
    time = new Date(+time + TIME_STEP);
    timeLogger.innerText = time.toString();

    const gmst = satellite.gstime(time);
    satData.forEach(d => {
        const eci = satellite.propagate(d.satrec, time);
        if (eci.position) {
            const gdPos = satellite.eciToGeodetic(eci.position, gmst);
            d.lat = satellite.radiansToDegrees(gdPos.latitude);
            d.lng = satellite.radiansToDegrees(gdPos.longitude);
            d.alt = gdPos.height / EARTH_RADIUS_KM;

            d.position = new THREE.Vector3(
                (EARTH_RADIUS_KM + d.alt) * Math.cos(d.lat * Math.PI / 180) * Math.cos(d.lng * Math.PI / 180),
                (EARTH_RADIUS_KM + d.alt) * Math.sin(d.lat * Math.PI / 180),
                (EARTH_RADIUS_KM + d.alt) * Math.cos(d.lat * Math.PI / 180) * Math.sin(d.lng * Math.PI / 180)
            );
        }
    });

    Globe.objectsData(satData);
}

function updateSatellites() {
    const toggleButton = document.getElementById('toggle-button');

    toggleButton.addEventListener('click', () => {
        console.log(satellitesMoving)
        satellitesMoving = !satellitesMoving;
        if (satellitesMoving) {
            intervalId = setInterval(update, TIME_STEP);
        } else {
            clearInterval(intervalId);
        }
    });
}

loadSatellites('./satellite.txt');

document.getElementById('toggle-general').addEventListener('click', () => {
    loadSatellites('./satellite.txt');
});

document.getElementById('toggle-communication').addEventListener('click', () => {
    loadSatellites('./communication_satellites.txt');
});

document.getElementById('toggle-navigation').addEventListener('click', () => {
    loadSatellites('./satellite_navigation.txt');
});

// Setup renderer
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth - 300, window.innerHeight); // Adjust for side panel width
document.getElementById('globeViz').appendChild(renderer.domElement);

// Setup scene
const scene = new THREE.Scene();
scene.add(Globe);
scene.add(new THREE.AmbientLight(0xcccccc, Math.PI));
scene.add(new THREE.DirectionalLight(0xffffff, 0.6 * Math.PI));

// Setup camera
const camera = new THREE.PerspectiveCamera();
camera.aspect = (window.innerWidth - 300) / window.innerHeight; // Adjust for side panel width
camera.updateProjectionMatrix();
camera.position.z = 400;

// Add camera controls
const tbControls = new TrackballControls(camera, renderer.domElement);
tbControls.minDistance = 101;
tbControls.zoomSpeed = 1;

// Raycaster for detecting mouse over and click objects
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onMouseMove(event) {
    // Update the mouse variable
    mouse.x = ((event.clientX - 300) / (window.innerWidth - 300)) * 2 - 1; // Adjust for side panel width
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    // Calculate objects intersecting the picking ray
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Globe.children);

    if (intersects.length > 0) {
        const intersectedObject = intersects[0].object;
        const satData = intersectedObject.userData.satData; // Retrieve satellite data from userData

        if (satData) {
            tooltip.style.display = 'block';
            tooltip.style.left = `${event.clientX / 1.5 + 10}px`;
            tooltip.style.top = `${event.clientY + 10}px`;
            tooltip.innerHTML = `Satellite: ${satData.name}<br>Latitude: ${satData.lat.toFixed(2)}<br>Longitude: ${satData.lng.toFixed(2)}`;
        }
    } else {
        tooltip.style.display = 'none';
    }
}

let lastClicked = 0;
function onClick(event) {
    const now = Date.now();
    if (now - lastClicked < 300) return; // Throttle clicks
    lastClicked = now;

    // Update the mouse variable
    mouse.x = ((event.clientX - 250) / (window.innerWidth - 250)) * 2 - 1; // Adjust for side panel width
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    // Calculate objects intersecting the picking ray
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Globe.children);

    if (intersects.length > 0) {
        const intersectedObject = intersects[0].object;
        const satData = intersectedObject.userData.satData; // Retrieve satellite data from userData
        console.log(satData);
        if (satData) {
            axios.post('http://127.0.0.1:5000', { satellite_name: satData.name }, {
                headers: { 'Content-Type': 'application/json' }
            })
                .then(response => {
                    const data = JSON.parse(response.data);
                    requestAnimationFrame(() => {
                        satelliteInfo.innerHTML = `<span class="lead-text">Satellite</span>: ${satData.name}<br><br>
                    <span class="lead-text">Country of Origin</span>: ${data.origin}<br><br>
                    <span class="lead-text">Cost</span>: ${data["cost"]}<br><br>
                    <span class="lead-text">Launch Date</span>: ${data["launch_date"]}<br><br>
                    <span class="lead-text">Purpose</span>: ${data["purpose"]}<br><br>
                    <span class="lead-text">History</span>: ${data["history"]}<br><br>
                    `;
                    });
                })
                .catch(error => {
                    console.error('Error:', error);
                    satelliteInfo.innerHTML = 'Sorry, could not get the satellite info';
                });
        }
    } else {
        satelliteInfo.innerHTML = 'Click on a satellite to see details here.';
    }
}

window.addEventListener('mousemove', onMouseMove, false);
window.addEventListener('click', onClick, false);

// Kick-off renderer
(function animate() {
    // Frame cycle
    tbControls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
})();