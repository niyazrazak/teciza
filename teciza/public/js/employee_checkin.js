// const os = require('os');




// function getMacAddress() {
//     const interfaces = os.networkInterfaces();
//     for (const name of Object.keys(interfaces)) {
//         for (const iface of interfaces[name]) {
//             if (iface.mac && iface.mac !== '00:00:00:00:00:00' && !iface.internal) {
//                 return iface.mac;
//             }
//         }
//     }
//     return null;
// }

// console.log(getMacAddress());