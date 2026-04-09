import { useEffect, useRef, useState } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';

const SATELLITE_NODES = {
  0: { name: "UAV Local Processing", lat: 30.1, lng: -90.1, alt: 0.05, color: "#10b981", type: "uav" }, // Ground/Edge
  1: { name: "Master Sat (Server)", lat: 38.0, lng: -95.0, alt: 0.4, color: "#ef4444", type: "master" },  // Far, High-powered
  2: { name: "Slave Sat 0", lat: 41.0, lng: -80.0, alt: 0.35, color: "#3b82f6", type: "slave" },
  3: { name: "Slave Sat 1", lat: 31.0, lng: -78.0, alt: 0.35, color: "#3b82f6", type: "slave" },
  4: { name: "Slave Sat 2", lat: 22.0, lng: -85.0, alt: 0.35, color: "#3b82f6", type: "slave" },
  5: { name: "Slave Sat 3", lat: 25.0, lng: -105.0, alt: 0.35, color: "#3b82f6", type: "slave" }
};

export default function GlobeSim({ activeTask }) {
  const globeRef = useRef();
  const [arcs, setArcs] = useState([]);
  
  // Create fixed satellite nodes
  const nodes = Object.values(SATELLITE_NODES);

  useEffect(() => {
    if (globeRef.current) {
      // Set initial camera position looking at the network
      globeRef.current.pointOfView({ lat: 25, lng: -80, altitude: 2.2 }, 1000);
      globeRef.current.controls().autoRotate = true;
      globeRef.current.controls().autoRotateSpeed = 0.5;
    }
  }, []);

  useEffect(() => {
    if (activeTask && activeTask.route !== undefined) {
      const uavLat = 30.0 + (parseFloat(activeTask.y) - 500) * 0.02; // Map 0-1000m to degrees
      const uavLng = -90.0 + (parseFloat(activeTask.x) - 500) * 0.02;

      // Update UAV "local" position so arcs originate correctly
      const uavPoint = { lat: uavLat, lng: uavLng, alt: 0.05 };
      SATELLITE_NODES[0].lat = uavLat;
      SATELLITE_NODES[0].lng = uavLng;

      const targetSat = SATELLITE_NODES[activeTask.route];
      
      if (!targetSat) return;

      const newArc = {
        startLat: uavLat,
        startLng: uavLng,
        endLat: targetSat.lat,
        endLng: targetSat.lng,
        color: ['#00ff00', targetSat.color]
      };

      setArcs(prev => [...prev.slice(-15), newArc]); // Keep last 15 arcs visible for trails
    }
  }, [activeTask]);

  return (
    <div className="w-full h-full relative cursor-move">
      <Globe
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        
        // Render Nodes (Satellites + UAV)
        customLayerData={nodes}
        customThreeObject={d => {
          const size = d.type === 'master' ? 4 : (d.type === 'uav' ? 2 : 3);
          const geom = new THREE.SphereGeometry(size, 16, 16);
          const mat = new THREE.MeshPhongMaterial({ color: d.color, emissive: d.color, emissiveIntensity: 0.5 });
          return new THREE.Mesh(geom, mat);
        }}
        customThreeObjectUpdate={(obj, d) => {
          Object.assign(obj.position, globeRef.current?.getCoords(d.lat, d.lng, d.alt));
        }}
        
        // Render Rings around nodes
        ringsData={nodes}
        ringLat="lat"
        ringLng="lng"
        ringAltitude="alt"
        ringColor="color"
        ringMaxRadius={d => d.type === 'master' ? 12 : 7}
        ringPropagationSpeed={3}
        ringRepeatPeriod={1000}

        // Render Arcs (Routing Decisions)
        arcsData={arcs}
        arcColor="color"
        arcDashLength={0.4}
        arcDashGap={0.2}
        arcDashInitialGap={() => Math.random()}
        arcDashAnimateTime={1000}
        arcAltitudeAutoScale={0.3}
        arcStroke={1.5}
      />
    </div>
  );
}
