# Supplier Payables

The legacy accounts-payable records of what the company buys from its suppliers and what it owes for it, inherited ahead of an ERP migration.

## Language

**Vendor**:
A supplier the company buys from and pays; one record per vendor.
_Avoid_: Supplier, company, account

**Tax ID**:
The government-issued identifier of a Vendor, used to recognise the same legal entity across records.
_Avoid_: VAT number, EIN, RFC

**Duplicate Vendor**:
Two or more Vendor records that refer to the same real-world supplier, typically revealed by a shared Tax ID.
_Avoid_: Dupe, repeat vendor

**Vendor Status**:
Whether a Vendor is currently allowed to be bought from: _active_ or _inactive_.
_Avoid_: State, flag

**Payment Terms**:
The agreement with a Vendor on how many days after an Invoice date payment is due (Net 30, Net 45, Net 60).
_Avoid_: Credit terms, due days

**Purchase Order**:
A commitment to buy goods or services from one Vendor for an agreed amount in a stated Currency.
_Avoid_: PO (in prose), order, requisition

**Currency**:
The money unit in which a Purchase Order is denominated: USD, CAD or MXN.
_Avoid_: Money type, FX

**Invoice**:
A Vendor's request for payment against a Purchase Order.
_Avoid_: Bill, payable

**Paid**:
The state of an Invoice that has been settled, as opposed to open.
_Avoid_: Settled, closed

**Orphan**:
A Purchase Order or Invoice whose Vendor or Purchase Order no longer exists in the records.
_Avoid_: Dangling record, broken link

**Country**:
The nation where a Vendor is based; the company deals with the United States, Canada and Mexico.
_Avoid_: Region, location

**Surviving Vendor**:
The one Vendor record kept when a group of Duplicate Vendors is merged into it.
_Avoid_: Master vendor, golden record, winner

**Quarantine**:
The holding area for records that cannot be loaded as they are, each kept with the reason it was set aside.
_Avoid_: Trash, reject pile, deleted
