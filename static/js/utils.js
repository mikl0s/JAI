// Function to show a temporary notification
export function showNotification(message, duration = 3000) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    // Show the notification
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 100);

    // Hide the notification after the specified duration
    setTimeout(() => {
        notification.style.opacity = '0';
        // Remove the notification from the DOM after the fade-out transition
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500); // Match the CSS transition time
    }, duration);
}

// TODO: Fetch this key from the server securely.  DO NOT leave it hardcoded in production.
export const hmacSecretKey = "d174ab988d3b9b65597e98957e02b355d174ab988d3b9b65597e98957e02b355";  // Replace with your actual secret key

export async function calculateHMAC(secretKey, method, path, body, timestamp) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secretKey);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  let message = method + path;
  if (body) {
      message += body;
  }
  message += timestamp;
  const messageData = encoder.encode(message);

  const signature = await crypto.subtle.sign("HMAC", key, messageData);
  const hexSignature = Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hexSignature;
}

export async function calculateProofOfWork(difficulty) {
  let nonce = 0;
  let hash;
  const targetPrefix = '0'.repeat(difficulty);
  do {
      nonce++;
      const data = `nonce:${nonce}`;
      const messageData = new TextEncoder().encode(data);
      hash = await crypto.subtle.digest('SHA-256', messageData);
      const hexHash = Array.from(new Uint8Array(hash))
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
  } while (!hexHash.startsWith(targetPrefix));
  return { nonce, hash: Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('') };
}

// Include the FingerprintJS library
export const fpPromise = import('https://openfpcdn.io/fingerprintjs/v4')
  .then(FingerprintJS => FingerprintJS.load());
