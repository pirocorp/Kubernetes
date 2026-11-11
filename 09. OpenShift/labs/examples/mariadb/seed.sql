CREATE TABLE IF NOT EXISTS quotes (
    id INT PRIMARY KEY,
    text VARCHAR(255) NOT NULL
);
INSERT INTO quotes (id, text) VALUES
    (1, 'OpenShift builds on Kubernetes'),
    (2, 'Services select Pods by labels'),
    (3, 'PVC stores data outside the Pod')
ON DUPLICATE KEY UPDATE text = VALUES(text);
SELECT id, text FROM quotes ORDER BY id;
