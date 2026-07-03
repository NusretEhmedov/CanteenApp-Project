USE CanteenDB;
GO


DROP TABLE IF EXISTS StockMovements;
DROP TABLE IF EXISTS Sales;
GO

DROP TABLE IF EXISTS Products;
GO

DROP TABLE IF EXISTS Suppliers;
GO

CREATE TABLE Suppliers (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100) NOT NULL,
    contact NVARCHAR(100),
    phone NVARCHAR(20),
    email NVARCHAR(100)
);

INSERT INTO Suppliers (name, contact, phone, email) 
VALUES 
('FreshBakes Co.', 'Sarah Jenkins', '555-0101', 'orders@freshbakes.com'),
('Global Drinks Ltd', 'Mike Ross', '555-0202', 'sales@globaldrinks.net'),
('GreenGrocer Direct', 'Elena Rodriguez', '555-0303', 'wholesale@greengrocer.com'),
('Pantry Staples Inc', 'David Chen', '555-0404', 'info@pantry-staples.com');

CREATE TABLE Products (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100) NOT NULL,
    category NVARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    stock_qty INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    supplier_id INT FOREIGN KEY REFERENCES Suppliers(id)
);

INSERT INTO Products (name, category, price, stock_qty, reorder_level, supplier_id) 
VALUES 
('Butter Croissant', 'Bakery', 2.50, 25, 10, 1),
('Chicken Mayo Sandwich', 'Fresh Food', 4.50, 15, 5, 1),
('Coca-Cola 500ml', 'Beverages', 1.80, 50, 15, 2),
('Sparkling Water 500ml', 'Beverages', 1.50, 40, 10, 2),
('Red Apple', 'Fruit', 0.80, 60, 20, 3),
('Banana', 'Fruit', 0.60, 45, 15, 3),
('Potato Chips 40g', 'Snacks', 1.20, 100, 30, 4),
('Chocolate Bar', 'Snacks', 1.50, 80, 20, 4); 

CREATE TABLE Sales (
    id INT PRIMARY KEY IDENTITY(1,1),
    product_id INT FOREIGN KEY REFERENCES Products(id),
    quantity INT NOT NULL,
    sale_date DATE DEFAULT GETDATE(),
    total_price DECIMAL(10,2)
);

INSERT INTO Sales (product_id, quantity, sale_date, total_price)
VALUES 
(1, 2, '2026-05-01', 5.00),
(3, 1, '2026-05-01', 1.80),
(2, 1, '2026-05-02', 4.50),
(7, 3, '2026-05-02', 3.60),
(5, 5, '2026-05-03', 4.00),
(8, 2, '2026-05-03', 3.00),
(4, 2, '2026-05-04', 3.00);

CREATE TABLE StockMovements (
    id INT PRIMARY KEY IDENTITY(1,1),
    product_id INT FOREIGN KEY REFERENCES Products(id),
    type NVARCHAR(3) CHECK (type IN ('IN','OUT')),
    quantity INT NOT NULL,
    movement_date DATE DEFAULT GETDATE(),
    note NVARCHAR(200)
);

INSERT INTO StockMovements (product_id, type, quantity, movement_date, note)
VALUES 
(1, 'IN', 30, '2026-04-30', 'Morning delivery from FreshBakes'),
(2, 'IN', 20, '2026-04-30', 'Morning delivery from FreshBakes'),
(5, 'OUT', 5, '2026-05-02', 'Spoiled/Bruised fruit discarded'),
(3, 'IN', 50, '2026-05-03', 'Monthly beverage restock'),
(7, 'OUT', 2, '2026-05-04', 'Returned by customer - Damaged packaging');
