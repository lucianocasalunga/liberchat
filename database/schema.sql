-- LiberChat Database Schema
-- Criado: 2025-12-08

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    npub VARCHAR(100) UNIQUE NOT NULL,
    pubkey VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    nip05 VARCHAR(100),
    picture_url TEXT,
    about TEXT,
    lightning_address VARCHAR(255),
    nwc_string TEXT, -- Nostr Wallet Connect
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);

-- Tabela de contatos
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    contact_pubkey VARCHAR(64) NOT NULL,
    contact_name VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, contact_pubkey)
);

-- Tabela de mensagens (cache local)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL, -- Nostr event ID
    sender_pubkey VARCHAR(64) NOT NULL,
    recipient_pubkey VARCHAR(64) NOT NULL,
    content TEXT NOT NULL, -- Mensagem criptografada (NIP-04)
    decrypted_content TEXT, -- Cache da mensagem descriptografada
    created_at TIMESTAMP NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Tabela de emblemas/badges
CREATE TABLE IF NOT EXISTS badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    satoshi_value INTEGER NOT NULL, -- Valor em satoshis
    rarity VARCHAR(50), -- bronze, silver, gold, diamond, royal, legendary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de transações de emblemas
CREATE TABLE IF NOT EXISTS badge_transactions (
    id SERIAL PRIMARY KEY,
    badge_id INTEGER REFERENCES badges(id),
    sender_id INTEGER REFERENCES users(id),
    recipient_id INTEGER REFERENCES users(id),
    satoshi_amount INTEGER NOT NULL,
    lightning_invoice TEXT,
    payment_hash VARCHAR(64),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de NFTs
CREATE TABLE IF NOT EXISTS nfts (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE, -- Nostr event ID (NIP-58)
    owner_id INTEGER REFERENCES users(id),
    creator_id INTEGER REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    image_url TEXT NOT NULL,
    metadata JSONB, -- Metadados adicionais
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configurações do usuário
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'auto', -- light, dark, auto
    language VARCHAR(10) DEFAULT 'pt', -- pt, en, es
    notifications_enabled BOOLEAN DEFAULT true,
    notifications_sound BOOLEAN DEFAULT true,
    privacy_dm_from VARCHAR(20) DEFAULT 'everyone', -- everyone, contacts, none
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_messages_sender ON messages(sender_pubkey);
CREATE INDEX idx_messages_recipient ON messages(recipient_pubkey);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_users_pubkey ON users(pubkey);
CREATE INDEX idx_users_npub ON users(npub);

-- Tabela de verificações NIP-05
CREATE TABLE IF NOT EXISTS nip05_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    pubkey VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    domain VARCHAR(100) DEFAULT 'libernet.app',
    verified BOOLEAN DEFAULT FALSE,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    CONSTRAINT username_format CHECK (username ~ '^[a-z0-9_-]+$')
);

CREATE INDEX IF NOT EXISTS idx_nip05_username ON nip05_verifications(username);
CREATE INDEX IF NOT EXISTS idx_nip05_verified ON nip05_verifications(verified);

-- Tabela de grupos (NIP-29 relay-based groups)
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(64) UNIQUE NOT NULL, -- h tag do grupo (Nostr)
    name VARCHAR(100) NOT NULL,
    description TEXT,
    picture_url TEXT,
    admin_pubkey VARCHAR(64) NOT NULL, -- Criador/admin principal
    relay_url VARCHAR(255), -- Relay dedicado do grupo (opcional)
    private BOOLEAN DEFAULT FALSE, -- Grupo privado ou público
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de membros de grupos
CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    user_pubkey VARCHAR(64) NOT NULL,
    role VARCHAR(20) DEFAULT 'member', -- admin, moderator, member
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP,
    UNIQUE(group_id, user_pubkey)
);

-- Tabela de mensagens de grupos (cache local)
CREATE TABLE IF NOT EXISTS group_messages (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL, -- Nostr event ID
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    sender_pubkey VARCHAR(64) NOT NULL,
    content TEXT NOT NULL, -- Mensagem em texto claro (grupos públicos) ou criptografada (grupos privados)
    parent_id VARCHAR(64), -- ID da mensagem pai (para respostas/threads)
    created_at TIMESTAMP NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para grupos
CREATE INDEX IF NOT EXISTS idx_groups_admin ON groups(admin_pubkey);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_pubkey);
CREATE INDEX IF NOT EXISTS idx_group_messages_group ON group_messages(group_id);
CREATE INDEX IF NOT EXISTS idx_group_messages_created ON group_messages(created_at DESC);

-- Tabela de doações
CREATE TABLE IF NOT EXISTS donations (
    id SERIAL PRIMARY KEY,
    user_pubkey VARCHAR(64) NOT NULL,
    amount_sats INTEGER NOT NULL,
    payment_hash VARCHAR(100) UNIQUE NOT NULL, -- OpenNode charge ID
    bolt11 TEXT NOT NULL, -- Invoice Lightning
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, expired, cancelled
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para doações
CREATE INDEX IF NOT EXISTS idx_donations_user ON donations(user_pubkey);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_paid_at ON donations(paid_at DESC);

-- Inserir emblemas padrão
INSERT INTO badges (name, description, satoshi_value, rarity) VALUES
('Bronze', 'Emblema de Bronze', 100, 'bronze'),
('Prata', 'Emblema de Prata', 500, 'silver'),
('Ouro', 'Emblema de Ouro', 1000, 'gold'),
('Diamante', 'Emblema de Diamante', 5000, 'diamond'),
('Real', 'Emblema Real', 10000, 'royal'),
('Lendário', 'Emblema Lendário', 50000, 'legendary')
ON CONFLICT DO NOTHING;
