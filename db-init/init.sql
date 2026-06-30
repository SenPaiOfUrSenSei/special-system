--
-- PostgreSQL database dump
--

\restrict 6cKC2aOqFzMfvwUb7bVhKE6IGkvQXiPRaJZyxBZn5epjNQaFoinza9kzlGzfMvJ

-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: executionstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.executionstatus AS ENUM (
    'INITIATED',
    'PENDING',
    'SUCCESS',
    'FAILED',
    'RETRYING'
);


ALTER TYPE public.executionstatus OWNER TO postgres;

--
-- Name: mandatestatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.mandatestatus AS ENUM (
    'INITIATED',
    'ACTIVE',
    'REJECTED',
    'REVOKED',
    'PAUSED',
    'EXPIRED'
);


ALTER TYPE public.mandatestatus OWNER TO postgres;

--
-- Name: notificationstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.notificationstatus AS ENUM (
    'PENDING',
    'SUCCESS',
    'FAILED'
);


ALTER TYPE public.notificationstatus OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: balances; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.balances (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    currency character varying NOT NULL,
    amount double precision NOT NULL
);


ALTER TABLE public.balances OWNER TO postgres;

--
-- Name: balances_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.balances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.balances_id_seq OWNER TO postgres;

--
-- Name: balances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.balances_id_seq OWNED BY public.balances.id;


--
-- Name: billers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.billers (
    id character varying NOT NULL,
    name character varying NOT NULL,
    category_name character varying NOT NULL,
    customer_params json NOT NULL
);


ALTER TABLE public.billers OWNER TO postgres;

--
-- Name: customer_fetch_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_fetch_sessions (
    id uuid NOT NULL,
    biller_id character varying NOT NULL,
    fetch_ref_id character varying NOT NULL,
    customer_params json NOT NULL,
    bills_data json,
    status character varying NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.customer_fetch_sessions OWNER TO postgres;

--
-- Name: debit_executions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.debit_executions (
    id uuid NOT NULL,
    mandate_id uuid NOT NULL,
    pre_debit_notification_id uuid,
    setu_debit_id character varying(100),
    amount_paise bigint NOT NULL,
    debited_amount_paise bigint,
    scheduled_at timestamp without time zone NOT NULL,
    executed_at timestamp without time zone,
    status public.executionstatus NOT NULL,
    retry_count integer NOT NULL,
    npci_response_code character varying(10),
    error_code character varying(50),
    error_message character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.debit_executions OWNER TO postgres;

--
-- Name: loans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loans (
    id uuid NOT NULL,
    mobile character varying NOT NULL,
    biller_id character varying NOT NULL,
    biller_name character varying NOT NULL,
    loan_account_number character varying NOT NULL,
    customer_name character varying NOT NULL,
    type character varying NOT NULL,
    total_outstanding integer NOT NULL,
    principal_outstanding integer NOT NULL,
    interest_outstanding integer NOT NULL,
    interest_rate double precision NOT NULL,
    remaining_tenure_months integer NOT NULL,
    dpd integer NOT NULL,
    status character varying NOT NULL,
    created_at timestamp without time zone,
    settled_at timestamp without time zone,
    settled_amount integer
);


ALTER TABLE public.loans OWNER TO postgres;

--
-- Name: otp_verifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.otp_verifications (
    id uuid NOT NULL,
    mobile character varying NOT NULL,
    otp_code character varying NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    is_verified boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.otp_verifications OWNER TO postgres;

--
-- Name: pre_debit_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pre_debit_notifications (
    id uuid NOT NULL,
    mandate_id uuid NOT NULL,
    setu_notification_id character varying(100),
    amount_paise bigint NOT NULL,
    scheduled_at timestamp without time zone NOT NULL,
    sent_at timestamp without time zone,
    expected_debit_date date NOT NULL,
    status public.notificationstatus NOT NULL,
    error_code character varying(50),
    error_message character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.pre_debit_notifications OWNER TO postgres;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id uuid NOT NULL,
    fetch_session_id uuid NOT NULL,
    payment_ref_id character varying,
    amount integer NOT NULL,
    payment_gateway character varying NOT NULL,
    status character varying NOT NULL,
    created_at timestamp without time zone,
    completed_at timestamp without time zone,
    customer_name character varying NOT NULL,
    bill_number character varying NOT NULL,
    sender_id uuid,
    recipient_id uuid,
    source_currency character varying,
    target_currency character varying,
    source_amount double precision,
    target_amount double precision,
    tx_hash character varying,
    "timestamp" double precision
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: upi_mandates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.upi_mandates (
    id uuid NOT NULL,
    loan_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    reference_id character varying(100) NOT NULL,
    setu_mandate_id character varying(100),
    umn character varying(100),
    customer_vpa character varying(255),
    max_amount_paise bigint NOT NULL,
    amount_rule character varying(10),
    frequency character varying(30),
    start_date date NOT NULL,
    end_date date NOT NULL,
    status public.mandatestatus NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.upi_mandates OWNER TO postgres;

--
-- Name: user_consents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_consents (
    id uuid NOT NULL,
    mobile character varying NOT NULL,
    consent_id character varying NOT NULL,
    status character varying NOT NULL,
    fi_types json NOT NULL,
    expiry timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.user_consents OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    dob date NOT NULL,
    mobile character varying NOT NULL,
    pan character varying NOT NULL,
    tc_accepted boolean NOT NULL,
    created_at timestamp without time zone,
    credit_score integer,
    credit_utilization_ratio integer,
    total_active_accounts integer,
    payment_history_clean boolean,
    email character varying NOT NULL,
    username character varying NOT NULL,
    hashed_password character varying NOT NULL,
    preferred_currency character varying DEFAULT 'USDT'::character varying NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: balances id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balances ALTER COLUMN id SET DEFAULT nextval('public.balances_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
4484feb04090
\.


--
-- Data for Name: balances; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.balances (id, user_id, currency, amount) FROM stdin;
1	9fe8e842-31da-495d-b74a-87b7a8461dba	USDT	10000
3	9fe8e842-31da-495d-b74a-87b7a8461dba	ETH	10
4	9fe8e842-31da-495d-b74a-87b7a8461dba	SOL	100
6	0a55558e-cfd5-4a1f-b48a-093587798aec	USDC	10000
7	0a55558e-cfd5-4a1f-b48a-093587798aec	ETH	10
8	0a55558e-cfd5-4a1f-b48a-093587798aec	SOL	100
9	53d7b000-e5da-426b-a8c1-2c1850adbbdc	USDT	10000
10	53d7b000-e5da-426b-a8c1-2c1850adbbdc	USDC	10000
11	53d7b000-e5da-426b-a8c1-2c1850adbbdc	ETH	10
12	53d7b000-e5da-426b-a8c1-2c1850adbbdc	SOL	100
13	a1c9655e-3e86-4980-bc27-6f419a0850bc	USDT	10000
14	a1c9655e-3e86-4980-bc27-6f419a0850bc	USDC	10000
15	a1c9655e-3e86-4980-bc27-6f419a0850bc	ETH	10
16	a1c9655e-3e86-4980-bc27-6f419a0850bc	SOL	100
2	9fe8e842-31da-495d-b74a-87b7a8461dba	USDC	10099.95
5	0a55558e-cfd5-4a1f-b48a-093587798aec	USDT	9900
18	6595c728-9b85-427a-93d9-8c6926d687b9	USDC	10000
19	6595c728-9b85-427a-93d9-8c6926d687b9	ETH	10
20	6595c728-9b85-427a-93d9-8c6926d687b9	SOL	100
22	63973d4c-26f9-4f7d-8f99-fa480f0756ed	USDC	10000
23	63973d4c-26f9-4f7d-8f99-fa480f0756ed	ETH	10
24	63973d4c-26f9-4f7d-8f99-fa480f0756ed	SOL	100
17	6595c728-9b85-427a-93d9-8c6926d687b9	USDT	10099.95
21	63973d4c-26f9-4f7d-8f99-fa480f0756ed	USDT	9900
\.


--
-- Data for Name: billers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.billers (id, name, category_name, customer_params) FROM stdin;
HDFC00000NAT01	HDFC Loan Services	loan-repayment	[{"paramName": "Loan Account Number", "dataType": "NUMERIC", "minLength": 8, "maxLength": 12, "optional": false, "regex": "^[0-9]{8,12}$", "visibility": true}, {"paramName": "Mobile Number", "dataType": "NUMERIC", "minLength": 10, "maxLength": 10, "optional": false, "regex": "^[0-9]{10}$", "visibility": true}]
ADIT00000NAT02	Aditya Birla Finance	loan-repayment	[{"paramName": "Loan Account Number", "dataType": "NUMERIC", "minLength": 6, "maxLength": 10, "optional": false, "regex": "^[0-9]{6,10}$", "visibility": true}, {"paramName": "Mobile Number", "dataType": "NUMERIC", "minLength": 10, "maxLength": 10, "optional": false, "regex": "^[0-9]{10}$", "visibility": true}]
SBIL00000NAT03	SBI Loans	loan-repayment	[{"paramName": "Loan Account Number", "dataType": "NUMERIC", "minLength": 8, "maxLength": 12, "optional": false, "regex": "^[0-9]{8,12}$", "visibility": true}, {"paramName": "Mobile Number", "dataType": "NUMERIC", "minLength": 10, "maxLength": 10, "optional": false, "regex": "^[0-9]{10}$", "visibility": true}]
\.


--
-- Data for Name: customer_fetch_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customer_fetch_sessions (id, biller_id, fetch_ref_id, customer_params, bills_data, status, created_at) FROM stdin;
979dbe10-4972-4fa0-9c88-9b9a39710000	HDFC00000NAT01	MOCK-FETCH-REF-001	{"mobile": "9876543210"}	\N	SUCCESS	2026-06-29 00:00:00
64b95e45-8ee8-43e2-9d86-2731692b81e1	ADIT00000NAT02	FETCH-4F501CF9469148E9	{"Loan Account Number": "1895159"}	[{"amount": 850000, "billNumber": "ABF-EMI-101", "billPeriod": "MONTHLY", "dueDate": "2026-07-01", "billDate": "2026-06-01", "customerName": "Manoj Chekuri"}]	SUCCESS	2026-06-29 00:32:26.56193
\.


--
-- Data for Name: debit_executions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.debit_executions (id, mandate_id, pre_debit_notification_id, setu_debit_id, amount_paise, debited_amount_paise, scheduled_at, executed_at, status, retry_count, npci_response_code, error_code, error_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loans (id, mobile, biller_id, biller_name, loan_account_number, customer_name, type, total_outstanding, principal_outstanding, interest_outstanding, interest_rate, remaining_tenure_months, dpd, status, created_at, settled_at, settled_amount) FROM stdin;
a6340d60-d760-45cf-bda0-85f18e9b01a7	9876543210	HDFC00000NAT01	HDFC Loan Services	12345678	Aarav Sharma	LOAN	150000000	120000000	30000000	10.5	36	95	ACTIVE	2026-06-29 00:04:21.477401	\N	\N
47e0e0a3-3e07-46fd-8b41-6f202bca21da	9876543210	ADIT00000NAT02	Aditya Birla Finance	1895159	Aarav Sharma	LOAN	85000000	70000000	15000000	12	24	45	ACTIVE	2026-06-29 00:04:21.483412	\N	\N
0ac05fdc-bc05-4ffe-b751-fddf67d2484d	9876543210	SBIL00000NAT03	SBI Loans	99999999	Aarav Sharma	LOAN	42000000	38000000	4000000	9.5	12	0	ACTIVE	2026-06-29 00:04:21.486489	\N	\N
242e13ab-7d7c-4480-b907-6485526f5415	9876543210	HDFC00000NAT01	HDFC Credit Services	4532XXXXXXXX1122	Aarav Sharma	CREDIT_CARD	12000000	9000000	3000000	42	0	110	ACTIVE	2026-06-29 00:04:21.488568	\N	\N
d8f7c794-b1a8-48c9-a3b7-f1cdd6266aa8	9999988888	SBIL00000NAT03	SBI Loans	1111222233	Priya Patel	LOAN	500000000	450000000	50000000	8.75	180	15	ACTIVE	2026-06-29 00:04:21.49115	\N	\N
f0ce32c7-3445-4c3a-b83f-0fc2dc52a34d	9999988888	ADIT00000NAT02	Aditya Birla Finance	2222333344	Priya Patel	LOAN	35000000	30000000	5000000	13.5	36	70	ACTIVE	2026-06-29 00:04:21.493671	\N	\N
\.


--
-- Data for Name: otp_verifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.otp_verifications (id, mobile, otp_code, expires_at, is_verified, created_at) FROM stdin;
f4588108-7157-4a09-8901-69275f4b8e58	9876223344	840173	2026-06-29 00:22:34.622858	t	2026-06-29 00:12:34.626956
c5dfd6ee-f10b-45ad-bb9a-fecf55bbe7d4	9876223344	663696	2026-06-29 00:22:49.070711	t	2026-06-29 00:12:49.07287
\.


--
-- Data for Name: pre_debit_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pre_debit_notifications (id, mandate_id, setu_notification_id, amount_paise, scheduled_at, sent_at, expected_debit_date, status, error_code, error_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transactions (id, fetch_session_id, payment_ref_id, amount, payment_gateway, status, created_at, completed_at, customer_name, bill_number, sender_id, recipient_id, source_currency, target_currency, source_amount, target_amount, tx_hash, "timestamp") FROM stdin;
e348b4c3-73c8-453f-bcc0-db51708213d3	979dbe10-4972-4fa0-9c88-9b9a39710000	\N	0	Bridgr L2 Engine	Completed	2026-06-29 00:15:34.650774	2026-06-29 00:15:34.650778	Bridgr User	BRIDGR-TX	0a55558e-cfd5-4a1f-b48a-093587798aec	9fe8e842-31da-495d-b74a-87b7a8461dba	USDT	USDC	100	99.95	0x8024c681c9d0d0a621243bbdd1f8b72f960de12efa7f1fb3912c0b18a9f7b6e4	1782692134.6462052
1b414a2b-2e6f-451d-94a4-0952139269b8	979dbe10-4972-4fa0-9c88-9b9a39710000	\N	0	Bridgr L2 Engine	Completed	2026-06-29 00:18:31.215425	2026-06-29 00:18:31.215435	Bridgr User	BRIDGR-TX	63973d4c-26f9-4f7d-8f99-fa480f0756ed	6595c728-9b85-427a-93d9-8c6926d687b9	USDT	USDT	100	99.95	0x1f20048b0748193da4113a0127d9cb77638efa964cafa143ad28c072b3298081	1782692311.2132044
527af37f-e9f8-4e9c-b7e0-44aa70b3bf2c	64b95e45-8ee8-43e2-9d86-2731692b81e1	PAY-E78B503A03EB471E	850000	GPay	SUCCESSFUL	2026-06-29 00:32:35.30921	2026-06-29 00:32:37.386025	Manoj Chekuri	ABF-EMI-101	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: upi_mandates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.upi_mandates (id, loan_id, customer_id, reference_id, setu_mandate_id, umn, customer_vpa, max_amount_paise, amount_rule, frequency, start_date, end_date, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_consents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_consents (id, mobile, consent_id, status, fi_types, expiry, created_at) FROM stdin;
479512c0-f3ab-4824-8a59-0de509954a64	9876543210	CNS-271A9F054409	ACTIVE	["LOAN", "CREDIT_CARD"]	\N	2026-06-29 00:22:38.79151
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, first_name, last_name, dob, mobile, pan, tc_accepted, created_at, credit_score, credit_utilization_ratio, total_active_accounts, payment_history_clean, email, username, hashed_password, preferred_currency) FROM stdin;
9fe8e842-31da-495d-b74a-87b7a8461dba	Priya	Patel	1993-05-20	9999988888	XYZWP9876Q	t	2026-06-29 00:04:21.498741	\N	\N	\N	\N	priya@example.com	priya	$2b$12$mEeEkMprrra8r8Y86exdEuKaCUmCR1h4iL91O307zLhDLb.gat1KO	USDC
0a55558e-cfd5-4a1f-b48a-093587798aec	Aarav	Sharma	1990-01-15	9876543210	ABCDE1234F	t	2026-06-29 00:04:21.498736	715	75	3	t	aarav@example.com	aarav	$2b$12$mEeEkMprrra8r8Y86exdEuKaCUmCR1h4iL91O307zLhDLb.gat1KO	USDT
53d7b000-e5da-426b-a8c1-2c1850adbbdc	Sanjay	Gupta	1990-01-01	9876123451	ABCDE5678F	t	2026-06-29 00:05:06.308315	715	75	3	t	sanjay@example.com	sanjay	$2b$12$mEeEkMprrra8r8Y86exdEuKaCUmCR1h4iL91O307zLhDLb.gat1KO	ETH
a1c9655e-3e86-4980-bc27-6f419a0850bc	Varun	Mehta	1994-08-25	9876223344	ABCDE9999Z	t	2026-06-29 00:12:38.373462	770	75	3	t	varun@example.com	varun	$2b$12$mEeEkMprrra8r8Y86exdEuKaCUmCR1h4iL91O307zLhDLb.gat1KO	SOL
6595c728-9b85-427a-93d9-8c6926d687b9	Aryan	Agarwal	2000-01-01	2692258322	SNNMH5590M	t	2026-06-29 00:17:38.318826	\N	\N	\N	\N	aryanagarwal0876@gmail.com	aryan	$2b$12$cSfWWDXTIgRe5RQJfVaJC.UBN7faRRv2hanxA2FH8yJyoDF7crK8K	USDT
63973d4c-26f9-4f7d-8f99-fa480f0756ed	Aryan	Agarwal	2000-01-01	2692294215	WIDZW7426N	t	2026-06-29 00:18:14.212888	\N	\N	\N	\N	aryanagarwal.0110@gmail.com	aryan2	$2b$12$77NXqD3gXjiggabM3t9IpeR5A7IxovO5pzU2hVxs2F7Gs3aoz1sbS	USDT
\.


--
-- Name: balances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.balances_id_seq', 24, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: balances balances_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balances
    ADD CONSTRAINT balances_pkey PRIMARY KEY (id);


--
-- Name: billers billers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billers
    ADD CONSTRAINT billers_pkey PRIMARY KEY (id);


--
-- Name: customer_fetch_sessions customer_fetch_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_fetch_sessions
    ADD CONSTRAINT customer_fetch_sessions_pkey PRIMARY KEY (id);


--
-- Name: debit_executions debit_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.debit_executions
    ADD CONSTRAINT debit_executions_pkey PRIMARY KEY (id);


--
-- Name: debit_executions debit_executions_setu_debit_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.debit_executions
    ADD CONSTRAINT debit_executions_setu_debit_id_key UNIQUE (setu_debit_id);


--
-- Name: loans loans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pkey PRIMARY KEY (id);


--
-- Name: otp_verifications otp_verifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otp_verifications
    ADD CONSTRAINT otp_verifications_pkey PRIMARY KEY (id);


--
-- Name: pre_debit_notifications pre_debit_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pre_debit_notifications
    ADD CONSTRAINT pre_debit_notifications_pkey PRIMARY KEY (id);


--
-- Name: pre_debit_notifications pre_debit_notifications_setu_notification_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pre_debit_notifications
    ADD CONSTRAINT pre_debit_notifications_setu_notification_id_key UNIQUE (setu_notification_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: upi_mandates upi_mandates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.upi_mandates
    ADD CONSTRAINT upi_mandates_pkey PRIMARY KEY (id);


--
-- Name: user_consents user_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consents
    ADD CONSTRAINT user_consents_pkey PRIMARY KEY (id);


--
-- Name: users users_pan_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pan_key UNIQUE (pan);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_balances_currency; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_balances_currency ON public.balances USING btree (currency);


--
-- Name: ix_balances_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_balances_id ON public.balances USING btree (id);


--
-- Name: ix_billers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_billers_id ON public.billers USING btree (id);


--
-- Name: ix_customer_fetch_sessions_fetch_ref_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_customer_fetch_sessions_fetch_ref_id ON public.customer_fetch_sessions USING btree (fetch_ref_id);


--
-- Name: ix_loans_loan_account_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loans_loan_account_number ON public.loans USING btree (loan_account_number);


--
-- Name: ix_loans_mobile; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_loans_mobile ON public.loans USING btree (mobile);


--
-- Name: ix_otp_verifications_mobile; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_otp_verifications_mobile ON public.otp_verifications USING btree (mobile);


--
-- Name: ix_pre_debit_notifications_expected_debit_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_pre_debit_notifications_expected_debit_date ON public.pre_debit_notifications USING btree (expected_debit_date);


--
-- Name: ix_transactions_payment_ref_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_payment_ref_id ON public.transactions USING btree (payment_ref_id);


--
-- Name: ix_transactions_tx_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_transactions_tx_hash ON public.transactions USING btree (tx_hash);


--
-- Name: ix_upi_mandates_reference_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_upi_mandates_reference_id ON public.upi_mandates USING btree (reference_id);


--
-- Name: ix_upi_mandates_setu_mandate_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_upi_mandates_setu_mandate_id ON public.upi_mandates USING btree (setu_mandate_id);


--
-- Name: ix_upi_mandates_umn; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_upi_mandates_umn ON public.upi_mandates USING btree (umn);


--
-- Name: ix_user_consents_consent_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_user_consents_consent_id ON public.user_consents USING btree (consent_id);


--
-- Name: ix_user_consents_mobile; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_consents_mobile ON public.user_consents USING btree (mobile);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_mobile; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_mobile ON public.users USING btree (mobile);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: balances balances_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balances
    ADD CONSTRAINT balances_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: customer_fetch_sessions customer_fetch_sessions_biller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_fetch_sessions
    ADD CONSTRAINT customer_fetch_sessions_biller_id_fkey FOREIGN KEY (biller_id) REFERENCES public.billers(id);


--
-- Name: debit_executions debit_executions_mandate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.debit_executions
    ADD CONSTRAINT debit_executions_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES public.upi_mandates(id) ON DELETE CASCADE;


--
-- Name: debit_executions debit_executions_pre_debit_notification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.debit_executions
    ADD CONSTRAINT debit_executions_pre_debit_notification_id_fkey FOREIGN KEY (pre_debit_notification_id) REFERENCES public.pre_debit_notifications(id);


--
-- Name: pre_debit_notifications pre_debit_notifications_mandate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pre_debit_notifications
    ADD CONSTRAINT pre_debit_notifications_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES public.upi_mandates(id) ON DELETE CASCADE;


--
-- Name: transactions transactions_fetch_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_fetch_session_id_fkey FOREIGN KEY (fetch_session_id) REFERENCES public.customer_fetch_sessions(id);


--
-- Name: transactions transactions_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: transactions transactions_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: upi_mandates upi_mandates_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.upi_mandates
    ADD CONSTRAINT upi_mandates_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 6cKC2aOqFzMfvwUb7bVhKE6IGkvQXiPRaJZyxBZn5epjNQaFoinza9kzlGzfMvJ

